/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { MlaPricelistPopup } from "@xas_pos_extend/app/utils/input_popups/mla_pricelist_popup";

// Función para cargar SweetAlert2 dinámicamente
function loadSweetAlert2() {
    return new Promise((resolve, reject) => {
        if (typeof Swal !== 'undefined') {
            resolve();
            return;
        }
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/sweetalert2@11';
        script.onload = () => {
            if (typeof Swal !== 'undefined') {
                resolve();
            } else {
                reject(new Error('SweetAlert2 no se cargó correctamente.'));
            }
        };
        script.onerror = () => reject(new Error('Error al cargar el script de SweetAlert2.'));
        document.head.appendChild(script);
    });
}

// Función original de show screen
const _origShowScreen = PosStore.prototype.showScreen;

patch(PosStore.prototype, {
    async _processData(loadedData){
        this.sale_condition_state = loadedData["sale.condition.state"];
        return await super._processData(loadedData);
    },

    /* SE COMENTA ESTE BLOQUEO YA QU ENO DEJABA ENTRAR A ORDENES DE VENTA DE DEVOLUCIÓN 25/08/2025 */
    showScreen(name, props) {
        // Si pidieron "ProductScreen" pero el POS es de cajero => forzar "TicketScreen"
        if (name === "ProductScreen" && this.config.xas_pos_role === "for_cashier") {
            /*ESTA CONDICION NOS PERMITE REALIZAR LAS DEVOLUCIONES, POR EL MOMENTO AUN LE FALTA ARREGLAR CUANDO SE NAVEGA ENTRE DEVOLUCION Y ORDENES ACTIVAS*/
            if (this.selectedOrder.amount_return > 0) {
                return _origShowScreen.call(this, "PaymentScreen", props);
            }
            return _origShowScreen.call(this, "TicketScreen", props);
        }
        return _origShowScreen.call(this, name, props);
    },

    calculatePrice(quantity, travelOption) {
        let price = 0;

        // En caso de recibir cantidades mayoristas
        if (quantity >= travelOption.xas_boxes_by_mayority) {
            price = travelOption.xas_mayority_price;

        // En caso de recibir cantidades menudistas
        } else {
            price = travelOption.xas_price_per_box;
        }
        return price;
    },

    calculateAffectOrder(quantity, travelOption){
        let affectOrder = false;
        // En caso de recibir cantidades mayoristas
        if (quantity >= travelOption.xas_boxes_by_mayority) {
            affectOrder = travelOption.xas_mayority_affect_orders;
        }
        return affectOrder;
    },

    async addProductToCurrentOrder(product, options = {}) {
        const updatedPricelists = await this.orm.call("product.product", "sync_mla_pricelists", [
            [product.id],
            this.company.id
        ]);
        if (updatedPricelists) {
            product.mla_pricelists = updatedPricelists;
        }

        const travelOptions = product.mla_pricelists;
        const order = this.get_order() || this.add_new_order();

        // Obtenemos data del producto
        const productInfo = await this.orm.call("product.product", "get_product_info_pos", [
            [product.id],
            product.get_price(order.pricelist, 1),
            1,
            this.config.id,
        ]);

        if (product.mla_pricelists.length == 0){
            try {
                await loadSweetAlert2();
                await Swal.fire("Las cantidades de este producto han sido agotadas por otra venta. Se actualizaran las existencias.");
                window.location.reload(); // Forzamos la recarga de la página para actualizar las existencias
            } catch (error) {
                console.error(error);
                alert("Algo no se encuentra bien. Por favor consulte a su administrador.");
            }
            return
        }

        // Invocamos el pop Up
        const { confirmed, payload } = await this.popup.add(MlaPricelistPopup, {
            productInfo: productInfo,
            product: product,
            travelOptions: travelOptions
        });

        // Recibimos la confirmación y lo que trae el payload
        if (confirmed){
            const quantities = payload.quantities;
            const confirmedTravelOptions = payload.travelOptions;

            // Creamos un mapa de las opciones de viaje
            const travelOptionMap = {};
            confirmedTravelOptions.forEach(travel => {
                travelOptionMap[travel.xas_mla_id] = travel;
            });

            for (const [mlaId, quantity] of Object.entries(quantities)) {
                if (quantity > 0) {
                    const travelOption = travelOptionMap[parseInt(mlaId, 10)];

                    if (travelOption) {
                        // Obtenemos nombre de viaje, cajas por pallet y precio de caja por pallet
                        const tripNumberName = travelOption.xas_trip_number_name;
                        const xasMlaId = travelOption.xas_mla_id;
                        const boxesPerPallet = travelOption.xas_boxes_by_pallet;
                        const availableQty = travelOption.xas_available_qty;

                        // Si boxesPerPallet es cero, tratamos todo como una sola línea
                        if (boxesPerPallet === 0) {
                            // Buscamos si ya existe una línea con el mismo producto, ID de MLA y sin estado de condición
                            const existingLine = order.orderlines.find(line => {
                                return line.product.id === product.id && 
                                       line.getXasMlaId() === xasMlaId &&
                                       !line.getXasSaleConditionState();
                            });

                            // Calculamos la cantidad total
                            let totalQuantity = (existingLine ? existingLine.quantity : 0) + quantity;

                            // Ajustamos la cantidad total si excede la disponible
                            if (totalQuantity > availableQty) {
                                totalQuantity = availableQty;
                            }

                            // Calculamos el precio según cantidad
                            const price = this.calculatePrice(totalQuantity, travelOption);
                            const xas_mayority_affect_orders = this.calculateAffectOrder(totalQuantity, travelOption);

                            // Actualizamos o creamos la línea
                            if (existingLine) {
                                existingLine.set_quantity(totalQuantity);
                                existingLine.set_unit_price(price);
                                existingLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);
                            } else {
                                order.add_product(product, {
                                    quantity: totalQuantity,
                                    price: price,
                                    extras: {
                                        xas_mayority_affect_orders: xas_mayority_affect_orders,
                                        xas_trip_number: tripNumberName,
                                        xas_product_pricelist_mla_id: xasMlaId,
                                        xas_stock_lot_id: travelOption.xas_stock_lot_id,
                                        xas_stock_lot_name: travelOption.xas_stock_lot_name,
                                    },
                                });
                            }
                        } else {
                            const palletPricePerBox = travelOption.xas_price_per_pallet;

                            // Buscamos si ya existen líneas con el mismo producto, ID de MLA y sin estado de condición
                            const existingPalletLine = order.orderlines.find(line => {
                                return line.product.id === product.id &&
                                       line.getXasMlaId() === xasMlaId &&
                                       line.get_quantity() >= boxesPerPallet &&
                                       !line.getXasSaleConditionState();
                            });
                            const existingSurplusLine = order.orderlines.find(line => {
                                return line.product.id === product.id &&
                                    line.getXasMlaId() === xasMlaId &&
                                    line.get_quantity() < boxesPerPallet &&
                                    !line.getXasSaleConditionState(); // Añadido: Solo fusionar si no hay estado
                            });
                            // Cantidades existentes
                            const existingPalletQuantity = existingPalletLine ? existingPalletLine.quantity : 0;
                            const existingSurplusQuantity = existingSurplusLine ? existingSurplusLine.quantity : 0; 
                            // Cantidad total sumando la nueva cantidad
                            let totalQuantity = existingPalletQuantity + existingSurplusQuantity + quantity;

                            // Ajustamos la cantidad total si excede la cantidad disponible
                            if (totalQuantity > availableQty) {
                                totalQuantity = availableQty;
                            }

                            // Calculamos cuántos pallets y sobrantes hay
                            const pallets = Math.floor(totalQuantity / boxesPerPallet);
                            const palletQuantity = pallets * boxesPerPallet;
                            const surplusQuantity = totalQuantity - palletQuantity;

                            // Actualizamos o creamos la línea de pallets
                            if (palletQuantity > 0) {
                                const xas_mayority_affect_orders = this.calculateAffectOrder(totalQuantity, travelOption);
                                if (existingPalletLine) {
                                    existingPalletLine.set_quantity(palletQuantity);
                                    existingPalletLine.set_unit_price(palletPricePerBox);
                                    existingPalletLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);
                                } else {
                                    order.add_product(product, {
                                        quantity: palletQuantity,
                                        price: palletPricePerBox,
                                        extras: {
                                            xas_mayority_affect_orders: xas_mayority_affect_orders,
                                            xas_trip_number: tripNumberName,
                                            xas_product_pricelist_mla_id: xasMlaId,
                                            xas_stock_lot_id: travelOption.xas_stock_lot_id,
                                            xas_stock_lot_name: travelOption.xas_stock_lot_name,
                                        },
                                    });
                                }
                            } else if (existingPalletLine) {
                                // Si no hay cantidad para pallets, eliminamos la línea de pallets existente
                                order.orderlines.remove(existingPalletLine);
                            }

                            // Actualizamos o creamos la línea de sobrantes
                            if (surplusQuantity > 0) {
                                const surplusPrice = this.calculatePrice(surplusQuantity, travelOption);
                                const xas_mayority_affect_orders = this.calculateAffectOrder(surplusQuantity, travelOption);
                                if (existingSurplusLine) {
                                    existingSurplusLine.set_quantity(surplusQuantity);
                                    existingSurplusLine.set_unit_price(surplusPrice);
                                    existingSurplusLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);
                                } else {
                                    order.add_product(product, {
                                        quantity: surplusQuantity,
                                        price: surplusPrice,
                                        extras: {
                                            xas_mayority_affect_orders: xas_mayority_affect_orders,
                                            xas_trip_number: tripNumberName,
                                            xas_product_pricelist_mla_id: xasMlaId,
                                            xas_stock_lot_id: travelOption.xas_stock_lot_id,
                                            xas_stock_lot_name: travelOption.xas_stock_lot_name,
                                        },
                                    });
                                }
                            } else if (existingSurplusLine) {
                                // Si no hay sobrantes, eliminamos la línea de sobrantes existente
                                order.orderlines.remove(existingSurplusLine);
                            }
                        }
                    }
                }
            }
            await order.apply_mayority_pricing();
        }
    },
});