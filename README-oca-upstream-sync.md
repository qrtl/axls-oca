# Keeping vendored OCA modules in step with upstream

This repo is a flat collection of addons copied out of various OCA repositories. Copies
drift: OCA fixes a bug, nobody notices for eight months, and the copy here quietly falls
behind. Noticing by hand every week does not happen.

`.github/workflows/oca-upstream-sync.yml` runs every Monday and reports the drift into a
single GitHub issue. It changes no code on a schedule — writing is always something a
person triggers.

## The problem this design exists to solve

The obvious version of this tool diffs each vendored module against upstream's branch
tip and opens a PR when they differ. That version is dangerous, because a two-way diff
cannot answer the only question that matters:

> Is this difference something OCA changed, or something _we_ changed?

Several modules here are patched on purpose. `auditlog` carries qrtl #172 and a
`tests/test_multi_company.py` that does not exist upstream; `purchase_invoice_plan`
carries a `i18n/ja.po` that upstream does not ship. A tool that cannot see the
difference will revert all of it, inside a bot PR that looks like every other routine
sync and gets waved through.

So every module gets a **baseline** in `.oca-sync-baselines.yml`: the upstream commit
the copy was taken from, plus a fingerprint of the copy as it stood at that moment. That
turns one useless diff into two useful ones:

```
diff(upstream@baseline, local copy)   -> what we changed
diff(upstream@baseline, upstream@tip) -> what OCA changed
```

Safety stops being a promise someone wrote in a config file and becomes a measurement
taken on every run. Nothing is auto-written unless the first diff is empty.

## Statuses

| status         | meaning                                                         | what happens                                       |
| -------------- | --------------------------------------------------------------- | -------------------------------------------------- |
| `up to date`   | matches upstream                                                | nothing                                            |
| `syncable`     | upstream moved; copy is byte-identical to its baseline          | `--apply` can update it; nothing local can be lost |
| `needs merge`  | upstream moved **and** the copy is patched                      | left alone; use `--merge`                          |
| `local only`   | copy differs but upstream has not moved                         | consider contributing it upstream                  |
| `unattributed` | no baseline, so the two diffs cannot be separated               | run `--discover-baselines`                         |
| `blocked`      | an overlay PR was closed unmerged, vanished, or stopped merging | left alone; a human decides                        |
| `not found`    | configured but missing here or upstream                         | fix the config                                     |

`unattributed` is the honest state for a copy nobody has attributed yet, not an error.
Modules leave it as they are adopted.

## Configuration

`.oca-sync.yml` is hand-written and says _what to track_:

```yaml
series: "16.0"

noise:
  - "i18n/*.po"
  - "README.rst"

sources:
  - repo: OCA/purchase-workflow
    modules:
      - name: purchase_invoice_plan
        overlays: []
```

`.oca-sync-baselines.yml` is machine-written and says _what was last synced_. Keeping
them apart means the generator never eats the comments in the file humans maintain.

### Noise

`noise` paths are still compared and still block an automatic sync — they are only
_counted separately_ in the report. `auditlog` differs from upstream in 84 files, of
which 73 are Transifex translation churn. Without the split, the 11 that are real code
are invisible.

### Overlay PRs

When a copy came from an OCA pull request that had not merged yet, say so:

```yaml
- name: purchase_invoice_plan
  overlays:
    - pr: 2500
```

Each run then re-checks that PR:

- **open** — merged onto the branch tip before comparing, so the copy is compared
  against what it is actually supposed to be.
- **merged** — not applied separately, but only after confirming the merge commit is
  genuinely an ancestor of this branch. "Merged" alone is not enough: a PR can merge to
  a different branch, or merge and be reverted.
- **closed without merging** — the module is marked `blocked` and left untouched. The
  code came from somewhere that no longer exists, and deleting functionality someone is
  using is not a decision a cron job should make.

## Usage

The weekly run needs nothing. By hand, from the Actions tab, _Run workflow_ with a mode;
or locally:

```bash
pip install pyyaml

# What has drifted?
python3 scripts/sync_oca_modules.py --check

# Adopt modules whose copies still match some upstream commit.
python3 scripts/sync_oca_modules.py --discover-baselines

# Update copies proved untouched (all syncable ones if none named).
python3 scripts/sync_oca_modules.py --apply purchase_exception

# Bring upstream into a patched copy, keeping the local work.
python3 scripts/sync_oca_modules.py --merge auditlog
```

`--apply` refuses anything not `syncable`, even when named explicitly.

`--merge` builds a real three-way merge — baseline as the common ancestor, our copy
against upstream's — so local changes survive and genuine clashes come back as conflict
markers rather than being silently resolved in upstream's favour. It is expected to
conflict sometimes; that is the tool working.

## Adopting the rest of the repo

Only the modules listed in `.oca-sync.yml` are looked at. Adding the other ~94 is the
actual work, and `--discover-baselines` does most of it: it walks upstream history
looking for the commit whose tree matches the local copy, so a pristine copy attributes
itself. A copy that matches nothing is patched, and says so.

Suggested order:

1. Add a batch of modules to `.oca-sync.yml` with `overlays: []`.
2. Run `--discover-baselines`, commit the result.
3. Run `--check` and read the report before enabling anything.

For a module that matches nothing, someone has to decide what the local changes are — a
deliberate patch worth keeping, or drift worth discarding — and either record a baseline
by hand or push the change upstream. There is no way to automate that judgement, which
is why the tool reports it instead of guessing.

## Known rough edges

- **CI does not run on the bot's PRs.** Branches pushed with `GITHUB_TOKEN` do not
  trigger other workflows. Close and reopen the PR, or push a commit, to make the test
  workflow fire. A PAT in a secret would avoid this at the cost of holding a PAT.
- **Regenerated files flip a module out of `syncable`.** If `oca-gen-addon-readme`
  rewrites `README.rst` after a sync, the copy no longer matches its baseline. The
  report shows it as `needs merge` with the churn confined to the `i18n/gen` column.
  Re-run `--apply` after committing the regeneration to re-baseline.
- **The right answer is sometimes to stop vendoring.** A module that is a pure upstream
  copy with no patches and no overlay does not need syncing so much as it needs to not
  be a copy: aggregate `OCA/<repo>` in `repos.yml` and upstream fixes arrive with
  `git pull`. That only applies to modules genuinely free of local changes, which is
  exactly what the report identifies.
