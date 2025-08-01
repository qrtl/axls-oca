/** @odoo-module **/

import {AnalyticDistribution} from "@analytic/components/analytic_distribution/analytic_distribution";
import {patch} from "web.utils";
import {useState} from "@odoo/owl";

patch(AnalyticDistribution.prototype, "custom.analytic_distribution.patch", {
    setup() {
        this._super(...arguments);
        this.relatedAccountIDs = useState([]);
    },

    async onSelect(option, params, tag) {
        await this._super(option, params, tag);
        const selectedIds = this.existingAnalyticAccountIDs;
        if (selectedIds.length) {
            const relatedIds = await this.orm.call(
                "account.analytic.account",
                "get_related_account_ids",
                [selectedIds]
            );
            this.relatedAccountIDs.splice(0);
            this.relatedAccountIDs.push(...relatedIds);
        }
    },

    async deleteTag(id, fromGroup) {
        await this._super(id, fromGroup);
        if (!this.existingAnalyticAccountIDs.length) {
            this.relatedAccountIDs.splice(0);
            return;
        }
        const relatedIds = await this.orm.call(
            "account.analytic.account",
            "get_related_account_ids",
            [this.existingAnalyticAccountIDs]
        );
        this.relatedAccountIDs.splice(0);
        this.relatedAccountIDs.push(...relatedIds);
    },

    analyticAccountDomain(groupId = null) {
        const domain = this._super(groupId);
        if (this.relatedAccountIDs.length) {
            domain.push(["id", "in", this.relatedAccountIDs]);
        }
        return domain;
    },
});
