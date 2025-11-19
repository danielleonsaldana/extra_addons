/** @odoo-module **/

import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { useService } from "@web/core/utils/hooks";
import { useAsyncLockedMethod } from "@point_of_sale/app/utils/hooks";

export class CustomPrintBillButton extends Component {
    static template = "xas_pos_extend.CustomPrintBillButton";

    setup() {
        this.pos = usePos();
        this.printer = useService("printer");
        this.click = useAsyncLockedMethod(this.click);
        this.isVisible = this.shouldShowBillButton();
    }

    // Función para validar el rol del punto de venta
    shouldShowBillButton() {
        if (this.pos.config.xas_pos_role === 'for_saler') {
            return false;
        } else if (this.pos.config.xas_pos_role === 'for_cashier') {
            return true;
        }
        return true;
    }

    _isDisabled() {
        const order = this.pos.get_order();
        if (!order) {
            return false;
        }
        return order.get_orderlines().length === 0;
    }

    async click() {
        const order = this.pos.get_order();
        if (!order) return;

        await this.pos.sendOrderInPreparationUpdateLastChange(order);

        (await this.printer.print(OrderReceipt, {
            data: this.pos.get_order().export_for_printing(),
            formatCurrency: this.env.utils.formatCurrency,
        })) || this.pos.showTempScreen("BillScreen");
    }
}

ProductScreen.addControlButton({
    component: CustomPrintBillButton,
    condition: function () {
        return true;
    },
});