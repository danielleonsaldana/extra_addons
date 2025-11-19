/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { onMounted, useRef, useState } from "@odoo/owl";

export class DateInputPopup extends AbstractAwaitablePopup {
    static template = "xas_pos_extend.DateInputPopup";
    static defaultProps = {
        confirmText: _t("Confirm"),
        cancelText: _t("Cancel"),
        confirmKey: "Enter",
        title: _t("Select a Date"),
        placeholder: _t("YYYY-MM-DD"),
        startingValue: "",
    };

    setup() {
        super.setup();
        this.state = useState({ inputValue: this.props.startingValue });
        this.inputRef = useRef("input");
        onMounted(this.onMounted);
    }

    _onWindowKeyup(event) {
        if (event.key === this.props.confirmKey) {
            this.confirm();
        } else {
            super._onWindowKeyup(...arguments);
        }
    }

    onMounted() {
        this.inputRef.el.focus();
    }

    getPayload() {
        return this.state.inputValue;
    }
}