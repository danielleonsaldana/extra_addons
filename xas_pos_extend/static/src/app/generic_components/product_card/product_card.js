/** @odoo-module **/

import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(ProductCard.prototype, {

    setup() {
        super.setup();
        this.pos = usePos();
        this.isVisible = this.shouldShowButton();
    },

    // Función para validar el rol del punto de venta
    shouldShowButton() {

        let notshow;
        if (this.pos.config.xas_pos_role === 'for_saler') {
            notshow = true;
        } else if (this.pos.config.xas_pos_role === 'for_cashier') {
            notshow = false;
        } else {
            notshow = false;
        }

        return notshow;
    }
});