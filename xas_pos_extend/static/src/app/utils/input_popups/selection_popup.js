/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class SelectionPopup extends AbstractAwaitablePopup {
    static template = "xas_pos_extend.SelectionPopup";
    static defaultProps = {
        confirmText: _t("Confirm"),
        cancelText: _t("Cancel"),
        confirmKey: "Enter",
        title: _t("Select an Option"),
        options: [],
    };

    setup() {
        super.setup();
        this.state = useState({ optionSelected: null });
    }

    _onWindowKeyup(event) {
        if (event.key === this.props.confirmKey) {
            this.confirm();
        } else {
            super._onWindowKeyup(...arguments);
        }
    }

    getPayload() {
        return this.state.optionSelected;
    }
}