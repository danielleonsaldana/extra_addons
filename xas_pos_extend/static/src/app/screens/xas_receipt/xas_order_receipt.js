/** @odoo-module **/

import { Component } from "@odoo/owl";
import { omit } from "@web/core/utils/objects";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { ReceiptHeader } from "@point_of_sale/app/screens/receipt_screen/receipt/receipt_header/receipt_header";

/**
 * Recibo especial para POS de tipo “cajero”.
 * Solo cambia la plantilla; la data y los helpers son los mismos
 * que usa OrderReceipt.
 */
export class XasOrderReceipt extends Component {
    static template = "xas_pos_extend.XasOrderReceipt";          // ← tu QWeb
    static components = { Orderline, OrderWidget, ReceiptHeader };
    static props = { data: Object, formatCurrency: Function };

    omit(...args) {
        return omit(...args);
    }
}