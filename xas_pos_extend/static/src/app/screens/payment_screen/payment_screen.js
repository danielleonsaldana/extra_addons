/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { useService } from "@web/core/utils/hooks";
// En caso de requerir un ticket custom, lo podemos mandar a llamar
//import { XasOrderReceipt } from "@xas_pos_extend/app/screens/xas_receipt/xas_order_receipt";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.orm = this.env.services.orm;
        this.printer = useService("printer");
    },

    // Sobreescribir validateOrder para incluir la lógica de eval_lifetime
    async validateOrder(isForceValidate) {
        // Asignar la fecha al pedido actual
        const today = new Date();
        const shippingDate = today.getFullYear() + '-' +
                    String(today.getMonth() + 1).padStart(2, '0') + '-' +
                    String(today.getDate()).padStart(2, '0');
        this.currentOrder.setShippingDate(shippingDate);

        this.numberBuffer.capture();

        // Asegurarse de que el pedido está sincronizado
        if (!this.currentOrder.backendId) {
            await this.pos.push_single_order(this.currentOrder); // Enviar la orden al servidor
        }

        // Llamar a la función Python eval_lifetime para revisar la validez de la orden
        const isValid = await this.orm.call("pos.order", "eval_lifetime", [this.currentOrder.server_id]);

        // Caso de no ser valida lanzamos error
        if (!isValid) {
            this.popup.add(ErrorPopup, {
                title: _t("Orden no válida"),
                body: _t("Esta orden ya no es válida actualmente."),
            });
            return;
        }

        // Llamar al método original si la validación es exitosa
        return await super.validateOrder(isForceValidate);
    },

    do_invoiceable() {
        this.currentOrder.set_xas_is_invoiceable(!this.currentOrder.get_xas_is_invoiceable());
    },

    /**
     * Imprime OrderReceipt y manda a descargar el ticket 2,3,4. En caso de requerirse, podemos sobre escribir la función
     * para mostrar XasOrderReceipt en lugar de OrderReceipt.
     */
    async afterOrderValidation(suggestToSync = true) {
        await this._printBackendPdf();
        return await super.afterOrderValidation(suggestToSync);
        // Código original, necesario si sobre escribirmos
        this.pos.db.remove_unpaid_order(this.currentOrder);
        if (suggestToSync && this.pos.db.get_orders().length) {
            const { confirmed } = await this.popup.add(ConfirmPopup, {
                title: _t("Remaining unsynced orders"),
                body: _t("There are unsynced orders. Do you want to sync these orders?"),
            });
            if (confirmed) {
                // NOTE: Not yet sure if this should be awaited or not.
                // If awaited, some operations like changing screen
                // might not work.
                this.pos.push_orders();
            }
        }
        let nextScreen = this.nextScreen;
        if (
            nextScreen === "ReceiptScreen" &&
            !this.currentOrder._printed &&
            this.pos.config.iface_print_auto
        ) {
            const invoiced_finalized = this.currentOrder.is_to_invoice()
            ? this.currentOrder.finalized
            : true;

            if (invoiced_finalized) {
                // Aquí deje una condición para evaluar si el pos es cajero o vendedor y así imprimir el ticket 1 o el 2,3,4 de forma dinamica
                const ReceiptComponent =
                    this.pos.config.xas_pos_role === "for_cashier"
                        ? XasOrderReceipt
                        : OrderReceipt;

                const printResult = await this.printer.print(
                    ReceiptComponent,
                    {
                        data: this.pos.get_order().export_for_printing(),
                        formatCurrency: this.env.utils.formatCurrency,
                    },
                    { webPrintFallback: true }
                );

                if (printResult && this.pos.config.iface_print_skip_screen) {
                    this.pos.removeOrder(this.currentOrder);
                    this.pos.add_new_order();
                    nextScreen = "ProductScreen";
                }
            }
        }

        this.pos.showScreen(nextScreen);

        // Código del modulo 'pos_settle_due'
        const hasCustomerAccountAsPaymentMethod = this.currentOrder
            .get_paymentlines()
            .find((paymentline) => paymentline.payment_method.type === "pay_later");
        const partner = this.currentOrder.get_partner();
        if (hasCustomerAccountAsPaymentMethod && partner.total_due !== undefined) {
            this.pos.refreshTotalDueOfPartner(partner);
        }
    },

    async _printBackendPdf() {
        if (this.pos.config.xas_pos_role != 'for_cashier') {
            return;
        }
        await this.report.doAction("xas_pos_extend.action_report_pos_order", [
            this.currentOrder.server_id,
        ]);
    },
});