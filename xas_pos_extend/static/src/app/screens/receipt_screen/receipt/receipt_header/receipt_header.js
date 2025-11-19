/** @odoo-module **/

import { ReceiptHeader } from "@point_of_sale/app/screens/receipt_screen/receipt/receipt_header/receipt_header";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { patch } from "@web/core/utils/patch";
const { DateTime } = luxon;

patch(ReceiptHeader.prototype, {
    setup() {
        super.setup();

        // Cargamos el pos para obtener datos extras que necesitamos en la cabecera
        this.pos = usePos();

        // Cargamos la fecha de la orden y la formateamos obteniendola del pos
        this.currentOrder = this.pos.get_order();
        this.formattedDate = DateTime.fromISO(this.currentOrder.date_order).toFormat('dd/MM/yyyy HH:mm:ss');
        this.xas_cashier = this.pos.get_cashier();

        // Cargamos el cliente obteniendolo de la orden que obtenemos del pos.
        const partner = this.currentOrder.get_partner();
        this.client = partner;
    }
});
