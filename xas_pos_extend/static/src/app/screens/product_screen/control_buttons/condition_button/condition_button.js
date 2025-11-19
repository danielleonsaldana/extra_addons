/** @odoo-module **/

import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { SelectionPopup } from "@xas_pos_extend/app/utils/input_popups/selection_popup";
import { Component } from "@odoo/owl";
import { onWillStart } from "@odoo/owl";

export class ConditionButton extends Component {
    static template = "xas_pos_extend.ConditionButton";

    setup() {
        this.pos = usePos();
        this.user = useService("user");
        this.popup = useService("popup");
        onWillStart(async () => {
            const hasGroup_salesman = await this.user.hasGroup('xas_pos_extend.group_condition_sale_state_pos_salesman');
            const hasGroup_admin = await this.user.hasGroup('xas_pos_extend.group_condition_sale_state_pos_admin');
            if (hasGroup_salesman || hasGroup_admin){
                this.hasGroupEnableConditionButton = true;
            }
        });
    }

    async click() {
        const options = this.pos.sale_condition_state.map(condition => {
            return {
                id: condition.id,
                code: condition.code,
                name: condition.name,
            };
        });

        const { confirmed, payload: selectedCondition } = await this.popup.add(SelectionPopup, {
            title: ("Seleccione la condición del Producto"),
            options: options,
        });
 
        if (confirmed){
            // Obtener la orden activa y la línea seleccionada en el pedido
            const currentOrder = this.pos.get_order();
            const selectedOrderline = currentOrder.get_selected_orderline();

            if (selectedOrderline) {
                // Encontrar la condición completa usando el ID
                const condition = options.find(c => c.id == selectedCondition);
                if (condition) {
                    // Asignar la condición seleccionada a la línea de producto
                    selectedOrderline.setXasSaleConditionState(condition.id);
                    selectedOrderline.setXasSaleConditionStateName(`${condition.code} - ${condition.name}`);
                } else {
                    console.warn('Condición seleccionada no encontrada:', selectedCondition);
                }
            } else {
                console.warn('No hay ninguna línea de pedido seleccionada.');
            }
        }
    }

    isConditionButtonVisible() {
        if(this.hasGroupEnableConditionButton){
            if (this.pos.config.xas_pos_role === 'for_saler') {
                return false;
            }
        }
        return true;
    }

}

ProductScreen.addControlButton({
    component: ConditionButton,
    position: ["before", "SetFiscalPositionButton"],
    condition: function () {
        return true;
    },
});