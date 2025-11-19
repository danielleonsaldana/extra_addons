/** @odoo-module **/

import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(Numpad.prototype, {

    setup() {
        super.setup();
        this.pos = usePos();
        this.isVisibleNumPad = this.shouldShowNumPad();
    },

    // Función para validar el rol del punto de venta
    shouldShowNumPad() {

        /*14/08/2025 Se decide que el numpad se ve para todos*/
        /*let notshow;
        if (this.pos.config.xas_pos_role === 'for_saler') {
            notshow = false;
        } else if (this.pos.config.xas_pos_role === 'for_cashier') {
            notshow = true;
        } else {
            notshow = false;
        }*/
        let notshow;
        notshow = false
        return notshow;
    }
});