/** @odoo-module **/

import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { patch } from "@web/core/utils/patch";

patch(OrderReceipt.prototype, {
    setup() {
        super.setup();

        // Accedemos a la orden actual
        const order = this.props.data;
        // Importamos la biblioteca de QR code
        const qr = qrcode(4, 'Q');
        /*qr.addData(`QR_ORDER|${order.name}`);*/ /*04/08/2025 SE QUITA EL STRING A PETICION DE BETO*/
        qr.addData(`${order.name}`);
        qr.make();
        const qrCodeDataUrl = qr.createDataURL(8);

        // Guardamos el src del QR code generado y guardamos los terminos y condiciones
        this.customQRCodeSrc = qrCodeDataUrl;
    },
});