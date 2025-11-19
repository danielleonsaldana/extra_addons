/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";

export class SaleConditionStatePopup extends AbstractAwaitablePopup {
    static template = "xas_pos_extend.SaleConditionStatePopup";
    static defaultProps = {
        confirmText: _t("Confirm"),
        confirmKey: "Enter",
        title: _t("Condiciones de productos"),
        options: [],
    };

    setup() {
        super.setup();
    }

    _onWindowKeyup(event) {
        if (event.key === this.props.confirmKey) {
            this.confirm();
        } else {
            super._onWindowKeyup(...arguments);
        }
    }
}