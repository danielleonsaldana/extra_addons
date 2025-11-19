/** @odoo-module **/

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { SaleConditionStatePopup } from "@xas_pos_extend/app/navbar/sale_condition_state_popup/sale_condition_state_popup";
import { onWillStart } from "@odoo/owl";

patch(Navbar .prototype, {

    setup() {
        super.setup();
        this.user = useService("user");
        this.isVisibleProductImage = this.shouldShowProductImage();
        this.isVisibleCategoryImage = this.shouldShowCategoryImage();
        onWillStart(async () => {
            const hasGroup_salesman = await this.user.hasGroup('xas_pos_extend.group_condition_sale_state_pos_salesman');
            const hasGroup_admin = await this.user.hasGroup('xas_pos_extend.group_condition_sale_state_pos_admin');
            if (hasGroup_salesman || hasGroup_admin){
                this.isVisibleSaleConditionState = false;
            }else{
                this.isVisibleSaleConditionState = true;
            }
        });
    },

    // PopUp para mostrar condiciones de producto
    saleConditionStatePopup(){
        const options = this.pos.sale_condition_state.map(condition => {
            return {
                id: condition.code,
                label: condition.name,
            };
        });

        this.popup.add(SaleConditionStatePopup, {
            options: options,
        });
    },

    // Función para validar el rol del punto de venta
    shouldShowProductImage() {
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
    shouldShowCategoryImage() {
        let notshow;
        if (this.pos.config.xas_pos_role === 'for_saler') {
            notshow = false;
        } else if (this.pos.config.xas_pos_role === 'for_cashier') {
            notshow = true;
        } else {
            notshow = false;
        }

        return notshow;
    }
});