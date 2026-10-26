#!/usr/bin/env python3
"""Compare vendored OCA modules against their upstream branches.

The point of this script is to tell two things apart that a plain diff cannot:

    diff(upstream@baseline, local copy)   -> what *we* changed
    diff(upstream@baseline, upstream@tip) -> what *OCA* changed

Everything else follows from that. A module is only ever written automatically
when the first diff is empty -- proved by a recorded baseline, not asserted by a
human -- which is what stops an unattended job from reverting local work.

Comparison is done on git blob ids rather than file contents, so the upstream
clone can stay blobless and walking history costs no network at all.

Modes:

    --check                 report drift for every configured module (default)
    --discover-baselines    find the upstream commit a pristine copy came from
    --apply [MODULE...]     fast-forward copies that are provably untouched
    --merge MODULE          three-way merge upstream changes into a patched copy

See README-oca-upstream-sync.md.
"""

import argparse
import fnmatch
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = REPO_ROOT / ".oca-sync.yml"
BASELINE_FILE = REPO_ROOT / ".oca-sync-baselines.yml"
API = "https://api.github.com"

# Statuses, ordered by how much attention they deserve.
BLOCKED = "BLOCKED"
NEEDS_MERGE = "NEEDS_MERGE"
SYNCABLE = "SYNCABLE"
UNATTRIBUTED = "UNATTRIBUTED"
LOCAL_ONLY = "LOCAL_ONLY"
NOT_FOUND = "NOT_FOUND"
UP_TO_DATE = "UP_TO_DATE"

STATUS_ORDER = [
    BLOCKED,
    NEEDS_MERGE,
    SYNCABLE,
    UNATTRIBUTED,
    LOCAL_ONLY,
    NOT_FOUND,
    UP_TO_DATE,
]

STATUS_LABEL = {
    BLOCKED: "blocked",
    NEEDS_MERGE: "needs merge",
    SYNCABLE: "syncable",
    UNATTRIBUTED: "unattributed",
    LOCAL_ONLY: "local only",
    NOT_FOUND: "not found",
    UP_TO_DATE: "up to date",
}

EXPLANATIONS = {
    BLOCKED: "An overlay PR was closed unmerged, has vanished, or no longer merges "
    "cleanly. Nothing was touched. Decide whether to keep the code as a local patch, "
    "drop it, or point the overlay somewhere else.",
    NEEDS_MERGE: "Upstream moved **and** this copy is not a pristine copy of its "
    "baseline. Overwriting it would revert local work, so it is left alone; run "
    "`--merge` to bring upstream's changes in and resolve the rest by hand.",
    SYNCABLE: "Upstream moved and this copy is byte-identical to the baseline it was "
    "taken from, so nothing local can be lost. Safe to update automatically.",
    UNATTRIBUTED: "No baseline recorded, so upstream's changes cannot be told apart "
    "from local ones. Run `--discover-baselines`; if that finds nothing, the code "
    "itself is patched and a human has to record where it came from.",
    LOCAL_ONLY: "Differs from upstream, but upstream has not moved since the baseline. "
    "This is local work — consider contributing it upstream.",
    NOT_FOUND: "Configured but missing, either here or on the upstream branch. Check "
    "the config.",
}


def run(cmd, cwd=None, check=True):
    """Run a command, returning (stdout, returncode)."""
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            "command failed: {}\n{}".format(" ".join(cmd), proc.stderr or "")
        )
    return (proc.stdout or "").strip(), proc.returncode


def api_get(path):
    """GET a GitHub API path, returning parsed JSON, or None on 404."""
    request = urllib.request.Request(API + path)
    request.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------


def load_config():
    config = yaml.safe_load(CONFIG_FILE.read_text())
    series = str(config["series"])
    noise = config.get("noise") or []
    modules = []
    for source in config.get("sources") or []:
        for entry in source.get("modules") or []:
            modules.append(
                {
                    "repo": source["repo"],
                    "branch": str(source.get("branch") or series),
                    "name": entry["name"],
                    "overlays": [o["pr"] for o in entry.get("overlays") or []],
                }
            )
    return series, noise, modules


def load_baselines():
    if not BASELINE_FILE.exists():
        return {}
    return yaml.safe_load(BASELINE_FILE.read_text()) or {}


def save_baselines(baselines):
    header = (
        "# Generated by scripts/sync_oca_modules.py -- do not edit by hand.\n"
        "#\n"
        "# Each entry records the upstream commit a vendored copy was taken from, and a\n"
        "# fingerprint of the copy as it stood at that moment. The fingerprint is what\n"
        "# lets the weekly job prove a copy is still untouched before overwriting it.\n"
        "#\n"
        "# exact: true  -- the copy was byte-identical to that upstream commit, so an\n"
        "#                 overwrite can lose nothing, and the module can auto-sync.\n"
        "# exact: false -- the copy carried files of its own even then, so upstream\n"
        "#                 changes have to be merged rather than copied.\n\n"
    )
    BASELINE_FILE.write_text(
        header + yaml.safe_dump(baselines, default_flow_style=False, sort_keys=True)
    )


def key_for(module):
    return "{}/{}".format(module["repo"], module["name"])


# --------------------------------------------------------------------------
# Fingerprints
#
# Everything compares maps of {path: git blob id}. Git already content-addresses
# every file, so two maps are equal exactly when the trees are, and building one
# for an upstream commit needs only its tree objects -- never the file contents.
# --------------------------------------------------------------------------


def local_blobs(root):
    """Blob ids for every file under root, via a single git hash-object call."""
    if not root.is_dir():
        return None
    paths = [
        path
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    ]
    if not paths:
        return {}
    proc = subprocess.run(
        ["git", "hash-object", "--stdin-paths"],
        input="\n".join(str(p) for p in paths),
        stdout=subprocess.PIPE,
        check=True,
        text=True,
    )
    oids = proc.stdout.split()
    return {str(path.relative_to(root)): oid for path, oid in zip(paths, oids)}


def read_tree(root):
    """Return {relative path: bytes} for every file under root."""
    tree = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        tree[str(path.relative_to(root))] = path.read_bytes()
    return tree


def write_tree(tree, root):
    """Replace root with tree. The rmtree matters: files deleted upstream must go."""
    if root.exists():
        shutil.rmtree(root)
    for path, content in tree.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)


def is_noise(path, noise_globs):
    return any(fnmatch.fnmatch(path, pattern) for pattern in noise_globs)


def without_noise(blobs, noise_globs):
    return {p: o for p, o in blobs.items() if not is_noise(p, noise_globs)}


def fingerprint(blobs):
    """A short stable hash of a blob map, for recording in the baseline file."""
    hasher = hashlib.sha256()
    for path in sorted(blobs):
        hasher.update("{}\0{}\0".format(path, blobs[path]).encode())
    return hasher.hexdigest()[:16]


def compare(left, right, noise_globs):
    """Count differing paths between two blob maps, split into code and noise."""
    code = noise = 0
    for path in set(left) | set(right):
        if left.get(path) == right.get(path):
            continue
        if is_noise(path, noise_globs):
            noise += 1
        else:
            code += 1
    return code, noise


# --------------------------------------------------------------------------
# Upstream checkouts
# --------------------------------------------------------------------------


class Upstream:
    """A blobless clone of an upstream repo, shared by every module from it."""

    def __init__(self, workdir, repo, branch):
        self.repo = repo
        self.branch = branch
        self.path = Path(workdir) / repo.replace("/", "__")
        if not self.path.exists():
            run(
                [
                    "git",
                    "clone",
                    "--quiet",
                    "--filter=blob:none",
                    "--no-checkout",
                    "--branch",
                    branch,
                    "https://github.com/{}.git".format(repo),
                    str(self.path),
                ]
            )
        # Read the branch ref, not HEAD: tree() detaches HEAD to extract content.
        self.tip = run(
            ["git", "rev-parse", "refs/remotes/origin/{}".format(branch)], cwd=self.path
        )[0]
        self._resolved = {}
        self._sparse = False

    def blobs(self, ref, module):
        """Blob map for one module directory at a ref. Costs no blob fetches."""
        out, code = run(
            ["git", "ls-tree", "-r", "{}:{}".format(ref, module)],
            cwd=self.path,
            check=False,
        )
        if code != 0:
            return None
        blobs = {}
        for line in out.splitlines():
            meta, path = line.split("\t", 1)
            _mode, kind, oid = meta.split()
            if kind == "blob":
                blobs[path] = oid
        return blobs

    def tree(self, ref, module):
        """File contents for one module directory. This one does need the blobs.

        Done as a sparse checkout rather than `git archive`, because checkout
        batches the missing-blob fetch a partial clone needs into one request,
        where archive fetches them one at a time and takes minutes to do it.
        """
        if not self._sparse:
            run(["git", "sparse-checkout", "init", "--cone"], cwd=self.path)
            self._sparse = True
        run(["git", "sparse-checkout", "set", module], cwd=self.path)
        _out, code = run(
            ["git", "checkout", "--quiet", "--detach", ref], cwd=self.path, check=False
        )
        if code != 0 or not (self.path / module).is_dir():
            return None
        return read_tree(self.path / module)

    def commits_between(self, since, until, module):
        out, code = run(
            ["git", "rev-list", "--count", "{}..{}".format(since, until), "--", module],
            cwd=self.path,
            check=False,
        )
        return int(out) if code == 0 and out.isdigit() else None

    def find_baseline(self, module, local, noise_globs, limit=500):
        """Walk history for the upstream commit this local copy was taken from.

        Returns (sha, exact). ``exact`` means byte-identical to that commit -- the
        only case where a later overwrite can lose nothing. A code-only match
        (exact=False) still pins the baseline but records that the copy carries
        files of its own, such as a translation upstream does not ship. Finding
        nothing means the code itself is patched, which is the honest answer.
        """
        out, code = run(
            ["git", "rev-list", "--max-count={}".format(limit), self.tip, "--", module],
            cwd=self.path,
            check=False,
        )
        if code != 0 or not out:
            return None, False
        local_code = without_noise(local, noise_globs)
        fallback = None
        for sha in out.splitlines():
            blobs = self.blobs(sha, module)
            if blobs is None:
                continue
            if blobs == local:
                return sha, True
            if fallback is None and without_noise(blobs, noise_globs) == local_code:
                fallback = sha
        return fallback, False

    def resolve(self, module, overlays):
        """The ref representing upstream tip plus any open overlay PRs.

        Returns (ref, notes), or (None, notes) when the module must be left
        alone: a PR closed without merging, a PR that has vanished, or one that
        no longer merges cleanly. Guessing in any of those cases is how an
        unattended job silently removes functionality someone is using.
        """
        cache_key = (module, tuple(overlays))
        if cache_key in self._resolved:
            return self._resolved[cache_key]
        result = self._resolve(module, overlays)
        self._resolved[cache_key] = result
        return result

    def _resolve(self, module, overlays):
        notes = []
        if not overlays:
            return self.tip, notes

        to_merge = []
        for number in overlays:
            pull = api_get("/repos/{}/pulls/{}".format(self.repo, number))
            if pull is None:
                notes.append("PR #{} no longer exists".format(number))
                return None, notes
            head_sha = (pull.get("head") or {}).get("sha")
            if pull.get("merged"):
                merge_sha = pull.get("merge_commit_sha") or ""
                on_branch = (
                    merge_sha
                    and run(
                        ["git", "merge-base", "--is-ancestor", merge_sha, self.tip],
                        cwd=self.path,
                        check=False,
                    )[1]
                    == 0
                )
                if on_branch:
                    notes.append(
                        "PR #{} has merged and is already on {}".format(
                            number, self.branch
                        )
                    )
                else:
                    # Merged into some other branch, or merged and reverted.
                    notes.append(
                        "PR #{} is marked merged but its merge commit is not an "
                        "ancestor of {} — not applying it".format(number, self.branch)
                    )
                continue
            if pull.get("state") == "closed":
                notes.append(
                    "PR #{} is CLOSED WITHOUT MERGE — refusing to touch this "
                    "module".format(number)
                )
                return None, notes
            to_merge.append((number, head_sha))

        if not to_merge:
            return self.tip, notes

        head = self.tip
        for number, pr_head in to_merge:
            run(
                [
                    "git",
                    "fetch",
                    "--quiet",
                    "origin",
                    "refs/pull/{}/head".format(number),
                ],
                cwd=self.path,
                check=False,
            )
            if not pr_head or not self._has(pr_head):
                notes.append(
                    "PR #{} head is unreachable — it may have been force-pushed "
                    "or deleted".format(number)
                )
                return None, notes
            merged, code = run(
                ["git", "merge-tree", "--write-tree", head, pr_head],
                cwd=self.path,
                check=False,
            )
            if code != 0:
                notes.append(
                    "PR #{} does not merge cleanly onto {}".format(number, self.branch)
                )
                return None, notes
            head = self._commit_tree(merged.splitlines()[0], [head, pr_head], number)
            notes.append("PR #{} applied on top of {}".format(number, self.branch))
        return head, notes

    def _has(self, ref):
        return (
            run(["git", "cat-file", "-e", ref + "^{commit}"], self.path, False)[1] == 0
        )

    def _commit_tree(self, tree, parents, number):
        cmd = ["git", "commit-tree", tree]
        for parent in parents:
            cmd += ["-p", parent]
        cmd += ["-m", "overlay PR #{}".format(number)]
        env = dict(
            os.environ,
            GIT_AUTHOR_NAME="oca-sync",
            GIT_AUTHOR_EMAIL="oca-sync@invalid",
            GIT_COMMITTER_NAME="oca-sync",
            GIT_COMMITTER_EMAIL="oca-sync@invalid",
        )
        proc = subprocess.run(
            cmd,
            cwd=str(self.path),
            stdout=subprocess.PIPE,
            text=True,
            check=True,
            env=env,
        )
        return proc.stdout.strip()


# --------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------


def analyse(module, upstream, baselines, noise_globs):
    """Classify one module. This is the whole point of the script."""
    name = module["name"]
    result = {
        "repo": module["repo"],
        "name": name,
        "branch": module["branch"],
        "notes": [],
        "behind": None,
        "code": 0,
        "noise": 0,
        "target": None,
    }

    local = local_blobs(REPO_ROOT / name)
    if local is None:
        result["status"] = NOT_FOUND
        result["notes"].append("configured but not present in this repo")
        return result

    target, notes = upstream.resolve(name, module["overlays"])
    result["notes"].extend(notes)
    if target is None:
        result["status"] = BLOCKED
        return result
    result["target"] = target

    upstream_now = upstream.blobs(target, name)
    if not upstream_now:
        result["status"] = NOT_FOUND
        result["notes"].append(
            "no such module on {}/{}".format(module["repo"], module["branch"])
        )
        return result

    result["code"], result["noise"] = compare(local, upstream_now, noise_globs)

    baseline = baselines.get(key_for(module))
    if not baseline:
        result["status"] = UNATTRIBUTED
        result["notes"].append(
            "no baseline recorded, so upstream's changes cannot be told apart "
            "from local ones"
        )
        return result

    # Untouched since we recorded it...
    pristine = fingerprint(local) == baseline.get("fingerprint")
    # ...and what we recorded was an exact copy of upstream, so an overwrite can
    # lose nothing. A copy that already carried local files fails this even while
    # pristine, because those files are precisely what an overwrite destroys.
    exact = bool(baseline.get("exact"))
    result["behind"] = upstream.commits_between(
        baseline["upstream_sha"], upstream.tip, name
    )

    if result["code"] == 0 and result["noise"] == 0:
        result["status"] = UP_TO_DATE
    elif pristine and exact:
        result["status"] = SYNCABLE
    elif not result["behind"]:
        result["status"] = LOCAL_ONLY
    else:
        result["status"] = NEEDS_MERGE
        if not pristine:
            result["notes"].append("modified locally since the baseline was recorded")
        if not exact:
            result["notes"].append(
                "copy carries files upstream does not have; an overwrite would "
                "delete them"
            )
    return result


def three_way_merge(module, upstream, baseline, target):
    """Merge upstream's changes into a patched copy, preserving local work.

    A scratch repo gives us git's real merge: the baseline as common ancestor,
    our copy on one side, upstream's on the other. Conflicts come back as
    conflicts instead of being silently resolved in upstream's favour.
    """
    name = module["name"]
    local_path = REPO_ROOT / name
    base_tree = upstream.tree(baseline["upstream_sha"], name)
    if base_tree is None:
        return False, "baseline commit {} is unreachable".format(
            baseline["upstream_sha"][:12]
        )
    upstream_tree = upstream.tree(target, name)

    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "merge"
        scratch.mkdir()
        run(["git", "init", "--quiet", str(scratch)])
        run(["git", "checkout", "--quiet", "-b", "base"], cwd=scratch, check=False)
        run(["git", "config", "user.email", "oca-sync@invalid"], cwd=scratch)
        run(["git", "config", "user.name", "oca-sync"], cwd=scratch)

        def commit(tree, message):
            write_tree(tree, scratch / name)
            run(["git", "add", "-A"], cwd=scratch)
            run(
                ["git", "commit", "--quiet", "--allow-empty", "-m", message],
                cwd=scratch,
            )

        commit(base_tree, "upstream at baseline")
        run(["git", "checkout", "--quiet", "-b", "ours"], cwd=scratch)
        commit(read_tree(local_path), "our vendored copy")
        run(["git", "checkout", "--quiet", "-b", "theirs", "base"], cwd=scratch)
        commit(upstream_tree, "upstream now")
        run(["git", "checkout", "--quiet", "ours"], cwd=scratch)
        _out, code = run(
            ["git", "merge", "--no-edit", "theirs"], cwd=scratch, check=False
        )
        conflicts = run(
            ["git", "diff", "--name-only", "--diff-filter=U"], cwd=scratch, check=False
        )[0]
        write_tree(read_tree(scratch / name), local_path)

    if code != 0:
        return (
            False,
            "merged with conflicts, left in the working tree:\n  "
            + "\n  ".join(conflicts.splitlines()),
        )
    return True, "merged cleanly"


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def render(results, series, noise_globs):
    counts = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1

    lines = [
        "## OCA upstream drift — `{}`".format(series),
        "",
        "Checked {} against upstream.".format(
            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ),
        "",
        " · ".join(
            "**{}** {}".format(counts[s], STATUS_LABEL[s])
            for s in STATUS_ORDER
            if counts.get(s)
        ),
        "",
    ]

    actionable = [r for r in results if r["status"] != UP_TO_DATE]
    if not actionable:
        lines.append("Every configured module matches upstream. Nothing to do.")
        return "\n".join(lines)

    lines += [
        "| module | upstream | status | behind | code | i18n/gen |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for result in sorted(
        actionable, key=lambda r: (STATUS_ORDER.index(r["status"]), r["name"])
    ):
        lines.append(
            "| `{}` | {} | {} | {} | {} | {} |".format(
                result["name"],
                result["repo"],
                STATUS_LABEL[result["status"]],
                result["behind"] if result["behind"] is not None else "?",
                result["code"] or "—",
                result["noise"] or "—",
            )
        )
    lines.append("")

    for status in STATUS_ORDER:
        if counts.get(status) and status in EXPLANATIONS:
            lines.append(
                "**{}** — {}".format(STATUS_LABEL[status], EXPLANATIONS[status])
            )
            lines.append("")

    detailed = [r for r in actionable if r["notes"]]
    if detailed:
        lines += ["<details><summary>Per-module notes</summary>", ""]
        for result in detailed:
            lines.append("- `{}`".format(result["name"]))
            for note in result["notes"]:
                lines.append("  - {}".format(note))
        lines += ["", "</details>", ""]

    lines.append(
        "_`code` counts differing files outside {}; `i18n/gen` counts those inside "
        "it. Both are compared and both gate an automatic sync — the split only "
        "stops translation churn from hiding a real change._".format(
            ", ".join("`{}`".format(glob) for glob in noise_globs)
        )
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def emit(message):
    """Write a line of progress to stdout."""
    sys.stdout.write(message + "\n")


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


class Session:
    """Config, baselines and the upstream clones they need."""

    def __init__(self, workdir):
        self.series, self.noise, self.modules = load_config()
        self.baselines = load_baselines()
        self.workdir = workdir or tempfile.mkdtemp(prefix="oca-sync-")
        Path(self.workdir).mkdir(parents=True, exist_ok=True)
        self._upstreams = {}

    def upstream(self, module):
        key = (module["repo"], module["branch"])
        if key not in self._upstreams:
            self._upstreams[key] = Upstream(self.workdir, *key)
        return self._upstreams[key]

    def find(self, name):
        return next((m for m in self.modules if m["name"] == name), None)

    def analyse_all(self):
        return [
            analyse(module, self.upstream(module), self.baselines, self.noise)
            for module in self.modules
        ]


def cmd_discover(session):
    found = 0
    for module in session.modules:
        key = key_for(module)
        if key in session.baselines:
            continue
        local = local_blobs(REPO_ROOT / module["name"])
        if local is None:
            continue
        sha, exact = session.upstream(module).find_baseline(
            module["name"], local, session.noise
        )
        if not sha:
            emit(
                "{}: no matching upstream commit — the code itself is "
                "patched".format(module["name"])
            )
            continue
        session.baselines[key] = {
            "upstream_sha": sha,
            "fingerprint": fingerprint(local),
            "exact": exact,
            "recorded_at": today(),
            "how": (
                "discovered: byte-identical to this upstream commit"
                if exact
                else "discovered: code matches this upstream commit, but the copy "
                "carries files of its own"
            ),
        }
        found += 1
        emit(
            "{}: baseline {} ({})".format(
                module["name"],
                sha[:12],
                "exact" if exact else "code-only match, has local files",
            )
        )
    if found:
        save_baselines(session.baselines)
    emit("\n{} baseline(s) recorded.".format(found))
    return 0


def cmd_merge(session, name):
    module = session.find(name)
    if module is None:
        emit("not configured: {}".format(name))
        return 2
    baseline = session.baselines.get(key_for(module))
    if not baseline:
        emit("{}: no baseline, so there is nothing to merge against".format(name))
        return 2
    upstream = session.upstream(module)
    target, notes = upstream.resolve(name, module["overlays"])
    for note in notes:
        emit("  {}".format(note))
    if target is None:
        return 2
    ok, message = three_way_merge(module, upstream, baseline, target)
    emit("{}: {}".format(name, message))
    if ok:
        session.baselines[key_for(module)] = {
            "upstream_sha": target,
            "fingerprint": fingerprint(local_blobs(REPO_ROOT / name)),
            "exact": False,
            "recorded_at": today(),
            "how": "three-way merge of upstream into a locally patched copy",
        }
        save_baselines(session.baselines)
    return 0 if ok else 1


def cmd_apply(session, results, wanted):
    """Write only what the baselines prove cannot lose local work."""
    applied = []
    for module, result in zip(session.modules, results):
        if result["status"] != SYNCABLE:
            continue
        if wanted and module["name"] not in wanted:
            continue
        tree = session.upstream(module).tree(result["target"], module["name"])
        write_tree(tree, REPO_ROOT / module["name"])
        session.baselines[key_for(module)] = {
            "upstream_sha": result["target"],
            "fingerprint": fingerprint(local_blobs(REPO_ROOT / module["name"])),
            "exact": True,
            "recorded_at": today(),
            "how": "automatic sync of a copy proved untouched",
        }
        applied.append(module["name"])
        emit("{}: synced to {}".format(module["name"], result["target"][:12]))
    if applied:
        save_baselines(session.baselines)
    else:
        emit("nothing to apply.")
    return 0


def cmd_check(session, results, report_file):
    report = render(results, session.series, session.noise)
    emit(report)
    if report_file:
        Path(report_file).write_text(report + "\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as handle:
            handle.write(report + "\n")
    return 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Compare vendored OCA modules against upstream."
    )
    parser.add_argument("--check", action="store_true", help="report drift (default)")
    parser.add_argument(
        "--discover-baselines",
        action="store_true",
        help="record baselines for copies that still match an upstream commit",
    )
    parser.add_argument(
        "--apply",
        nargs="*",
        metavar="MODULE",
        help="update provably untouched copies (all syncable ones if none named)",
    )
    parser.add_argument(
        "--merge", metavar="MODULE", help="three-way merge upstream into a patched copy"
    )
    parser.add_argument("--report-file", help="also write the markdown report here")
    parser.add_argument("--workdir", help="where to cache upstream clones")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    session = Session(args.workdir)

    if args.discover_baselines:
        return cmd_discover(session)
    if args.merge:
        return cmd_merge(session, args.merge)

    results = session.analyse_all()
    if args.apply is not None:
        return cmd_apply(session, results, set(args.apply))
    return cmd_check(session, results, args.report_file)


if __name__ == "__main__":
    sys.exit(main())
