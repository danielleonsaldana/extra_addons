/** @odoo-module **/

import { SetPricelistButton } from "@point_of_sale/app/screens/product_screen/control_buttons/pricelist_button/pricelist_button";
import { patch } from "@web/core/utils/patch";

patch(SetPricelistButton .prototype, {

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