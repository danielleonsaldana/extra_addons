/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductInfoPopup } from "@point_of_sale/app/screens/product_screen/product_info_popup/product_info_popup";

patch(ProductInfoPopup.prototype, {
    setup() {
        super.setup(...arguments);
        // Tomamos las listas de precios MLA desde el producto
        const product = this.props.product || {};
        this.mlaPricelistData = product.mla_pricelists || [];
    },
});