/** @odoo-module **/

import { RefundButton } from "@point_of_sale/app/screens/product_screen/control_buttons/refund_button/refund_button";
import { patch } from "@web/core/utils/patch";

RefundButton.props = { "*": true };

patch(RefundButton.prototype, {

    setup() {
        super.setup();
        this.isVisible = this.shouldShowButton();
    },

    // Función para validar el rol del punto de venta
    shouldShowButton() {

        let notshow;
        if (this.pos.config.xas_pos_role === 'for_saler') {
            notshow = true;
        } else if (this.pos.config.xas_pos_role === 'for_cashier') {
            notshow = true;
        } else {
            notshow = false;
        }

        return notshow;
    }
});