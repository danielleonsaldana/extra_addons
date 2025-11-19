/** @odoo-module **/

import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { useBarcodeReader } from "@point_of_sale/app/barcode/barcode_reader_hook";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

patch(TicketScreen.prototype, {

    setup() {
        super.setup();
        this.isVisibleNewOrderButton = this.shouldShowNewOrderButton();
        useBarcodeReader({
            qr_order: this.onQrOrderScanned,
        });
    },

    async onQrOrderScanned(parsedBarcode) {
        const posReference = parsedBarcode.pos_reference;
        if (!posReference) {
            return;
        }
        // Sincronización de ordenes
        this._state.ui.searchDetails.fieldName = "RECEIPT_NUMBER";
        this._state.ui.searchDetails.searchTerm = posReference;
        await this._fetchSyncedOrders();

        // Busqueda local de orden
        const foundOrder = this.pos.get_order_list().find(
            (o) => o.name === posReference
        );
        if (foundOrder) {
            this._setOrder(foundOrder);
            return;
        }

        if (!foundOrder) {
            this.popup.add(ErrorPopup, {
                title: "No se pudo cargar la orden",
                body: `La orden con referencia ${posReference} no devolvió datos.`,
            });
            return;
        }
    },

    // Mostrar u ocultar el botón
    shouldShowNewOrderButton() {
        let notshow;
        if (this.pos.config.xas_pos_role === 'for_saler') {
            notshow = false;
        } else if (this.pos.config.xas_pos_role === 'for_cashier') {
            notshow = true;
        } else {
            notshow = false;
        }

        return notshow;
    },

    shouldHideDeleteButton(order) {
        let original_answ = super.shouldHideDeleteButton(order);
        if (this.pos.config.xas_pos_role === 'for_cashier'){
            original_answ = true;
        }
        return original_answ
    },

    getFilteredOrderList() {
        let orders = super.getFilteredOrderList();
        orders = orders.filter(o => o.get_orderlines().length > 0);
        return orders;
    },

    getXasMarkAsPaid(order) {
        return order.xas_mark_as_paid;
    },

    /*SE CREA ESTA FUNCION ASINCRONA PARA PODER SABER EN TIEMPO REAL CUANDO LA BANDERA DE COBRANZA ESTA ON/OFF*/
    async _get_xas_mark_as_paid(order, server_id) {
        const result = await (this.orm || this.pos.orm).call("pos.order", "get_pos_order_data", [[server_id], server_id]);        if (result.xas_mark_as_paid){
            order.xas_mark_as_paid = true
            return true
        }else{
            order.xas_mark_as_paid = false
            return false
        }
    },

    getStatus(order) {
        if (order.state == 'done') {
            return 'Pagado';
        }
        else{
            return 'En curso';
        }
    }

});