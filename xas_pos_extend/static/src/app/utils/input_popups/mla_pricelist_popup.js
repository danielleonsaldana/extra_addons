/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useState } from "@odoo/owl";

export class MlaPricelistPopup extends AbstractAwaitablePopup {
    static template = "xas_pos_extend.MlaPricelistPopup";
    static props = {
        confirmText: { type: String, optional: true },
        cancelText: { type: String, optional: true },
        confirmKey: { type: String, optional: true },
        title: { type: String, optional: true },
        travelOptions: { type: Array, optional: true },
        productInfo: { type: Object, optional: true },
        product: { type: Object, optional: true },
        "*": true,
    };
    static defaultProps = {
        confirmText: _t("Confirm"),
        cancelText: _t("Cancel"),
        confirmKey: "Enter",
        title: ("Seleccione el viaje"),
        travelOptions: [],
        productInfo: {},
        product: {},
    };

    setup() {
        super.setup();
        const travelOptions = this.props.travelOptions || [];
        this.state = useState({ 
            selectedTravel: null, 
            quantities: {}, 
            totalPrice: 0 
        });

        // Inicializar las cantidades a cero y calcular el precio inicial
        travelOptions.forEach(travel => {
            this.state.quantities[travel.xas_mla_id] = 0;
        });

        this.calculateTotalPrice();
    };

    increaseQuantity(mlaId) {
        // Buscar la opción de viaje correspondiente en travelOptions
        const travelOption = this.props.travelOptions.find(travel => travel.xas_mla_id === mlaId);

        // Si existe la opción de viaje y la cantidad es menor que xas_available_qty, permite el incremento
        if (typeof this.state.quantities[mlaId] !== 'undefined' && 
            travelOption && this.state.quantities[mlaId] < travelOption.xas_available_qty) {
            this.state.quantities[mlaId]++;
            this.calculateTotalPrice();
        }
    };

    decreaseQuantity(mlaId) {
        if (this.state.quantities[mlaId] > 0) {
            this.state.quantities[mlaId]--;
            this.calculateTotalPrice();
        }
    };

    calculateTotalPrice() {
        let total = 0;
        this.props.travelOptions.forEach(travel => {
            const quantity = this.state.quantities[travel.xas_mla_id] || 0;

            if (quantity >= travel.xas_boxes_by_pallet) {
                // Si la cantidad supera el umbral para precio por pallet
                const pallets = Math.floor(quantity / travel.xas_boxes_by_pallet);
                const remainingBoxes = quantity % travel.xas_boxes_by_pallet;
                total += pallets * travel.xas_boxes_by_pallet * travel.xas_price_per_pallet;

                // Calcular el precio restante de las cajas
                if (remainingBoxes >= travel.xas_boxes_by_mayority) {
                    total += remainingBoxes * travel.xas_mayority_price;
                } else {
                    total += remainingBoxes * travel.xas_price_per_box;
                }
            } else if (quantity >= travel.xas_boxes_by_mayority) {
                total += quantity * travel.xas_mayority_price;
            } else {
                total += quantity * travel.xas_price_per_box;
            }
        });

        this.state.totalPrice = total;
    };

    _onWindowKeyup(event) {
        if (event.key === this.props.confirmKey) {
            this.confirm();
        } else {
            super._onWindowKeyup(...arguments);
        }
    };

    getPayload() {
        const adjustedQuantities = {};
        // Ajustar la cantidad si supera la cantidad disponible
        this.props.travelOptions.forEach(travel => {
            const mlaId = travel.xas_mla_id;
            const quantity = this.state.quantities[mlaId] || 0;
            const availableQty = travel.xas_available_qty || 0;
            adjustedQuantities[mlaId] = Math.min(quantity, availableQty);
        });
        return {
            travelOptions: this.props.travelOptions,
            quantities: adjustedQuantities,
        };
    };
}