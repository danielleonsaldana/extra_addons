/** @odoo-module **/

import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { SelectionPopup } from "@xas_pos_extend/app/utils/input_popups/selection_popup";
import { useService } from "@web/core/utils/hooks";
import { onWillStart } from "@odoo/owl";

ProductScreen.props = { "*": true };

patch(ProductScreen.prototype, {

    setup() {
        this.user = useService("user");
        this.popup = useService("popup");
        super.setup();
        this.isVisibleRightPanel = this.shouldShowRightPanel();
        onWillStart(async () => {
            const hasGroup = await this.user.hasGroup('xas_pos_extend.group_enable_edit_product_price_pos');
            const hasGroup_salesman = await this.user.hasGroup('xas_pos_extend.group_condition_sale_state_pos_salesman');
            const hasGroup_admin = await this.user.hasGroup('xas_pos_extend.group_condition_sale_state_pos_admin');
            if (hasGroup_salesman || hasGroup_admin){
                this.hasGroupEnableConditionButton = true;
            }
            this.hasGroupEnableEditProductPricePos = hasGroup;
        });
    },

    // Función para validar el rol del punto de venta
    getNumpadButtons() {
        let data = super.getNumpadButtons();
        if (!this.hasGroupEnableEditProductPricePos){
            data[11]['text'] = ' ';
            data[11]['disabled'] = true;
        }
        if (this.pos.config.xas_pos_role === 'for_saler') {
            data[7]['text'] = ' ';
            data[7]['disabled'] = true;
        }
        return data;
    },
    // Mostrar u ocultar panel derecho
    shouldShowRightPanel() {
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

    // Herencia para mostrar condiciones de venta cuando intenten editar el precio
    async onNumpadClick(buttonValue){
        super.onNumpadClick(buttonValue);
        if (buttonValue === "price" && this.hasGroupEnableConditionButton) {
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
    
            if (confirmed) {
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
    },

    // Calculamos los precios de producto
    calculatePrice(quantity, travelOption) {
        let price = 0;

        // Cantidades mayoristas
        if (quantity >= travelOption.xas_boxes_by_mayority) {
            price = travelOption.xas_mayority_price;
        } else {
            // Cantidades menudistas
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

    async updateSelectedOrderline({ buffer, key }) {
        // Llamar al método original primero
        await super.updateSelectedOrderline({ buffer, key });
        const order = this.pos.get_order();
        const selectedLine = order.get_selected_orderline();

        if (this.pos.numpadMode === 'quantity' && selectedLine) {
            /* Obtenemos el ID de MLA y la información que necesitamos de él*/
            const tripNumberName = selectedLine.getXasTripNumber();
            const xasMlaId = selectedLine.getXasMlaId();
            const product = selectedLine.get_product();
            const mlaPricelists = product.mla_pricelists;
            if (!mlaPricelists || mlaPricelists.length === 0) {
                return;
            }
            const travelOption = mlaPricelists.find(option => option.xas_mla_id === xasMlaId);
            if (!travelOption) {
                return;
            }

            // Parsear la nueva cantidad ingresada
            let newQuantity = parseFloat(buffer);
            // Añadido: Verificar si la línea ya tiene un estado de condición
            const currentSaleCondition = selectedLine.getXasSaleConditionState();
            if (currentSaleCondition) {
                // Si tiene condición, solo actualizamos cantidad respetando el límite disponible
                const availableQty = travelOption.xas_available_qty;
                if (newQuantity > availableQty) {
                    newQuantity = availableQty;
                }
                selectedLine.set_quantity(newQuantity);
                // Mantenemos el precio y estado existentes, no aplicamos lógica de pallet/fusión
                this.numberBuffer.capture();
                await order.apply_mayority_pricing();
                return true; 
            }
            // En caso de ser borrar, usamos la funcionalidad nativa
            if (key === "Backspace") {
                selectedLine.setXasMayorityAffectOrders(this.calculateAffectOrder(newQuantity, travelOption))
                await order.apply_mayority_pricing();
                return;
            }

            if (isNaN(newQuantity) || newQuantity < 0) {
                // Entrada inválida, reiniciar el buffer y mostrar un error
                this.numberBuffer.reset();
                await this.popup.add(ErrorPopup, {
                    title: 'Cantidad inválida',
                    body: 'Por favor, ingrese una cantidad válida.',
                });
                return;
            }

            // Obtener la cantidad disponible
            const availableQty = travelOption.xas_available_qty;

            // Verificar si la cantidad excede la disponible
            if (newQuantity > availableQty) {
                newQuantity = availableQty;
            }

            // Proceder a recalcular precios basados en la nueva cantidad
            const boxesPerPallet = travelOption.xas_boxes_by_pallet;

            // Si boxesPerPallet es cero, tratamos todo como una sola línea
            if (boxesPerPallet === 0) {
                // Buscamos si ya existe otra línea con el mismo producto, ID de MLA y MISMO estado de condición
                const existingLine = order.orderlines.find(line => {
                    return line.product.id === product.id && 
                           line.getXasMlaId() === xasMlaId &&
                           line.getXasSaleConditionState() === currentSaleCondition && // Añadido: verificar estado
                           line !== selectedLine;
                });

                // Calculamos la cantidad total
                let totalQuantity = (existingLine ? existingLine.quantity : 0) + newQuantity;

                // Ajustamos la cantidad total si excede la disponible
                if (totalQuantity > availableQty) {
                    totalQuantity = availableQty;
                }

                // Calculamos el precio según cantidad
                const price = this.calculatePrice(totalQuantity, travelOption);

                // Actualizamos o fusionamos líneas
                if (existingLine) {
                    const xas_mayority_affect_orders = this.calculateAffectOrder(totalQuantity, travelOption);
                    existingLine.set_quantity(totalQuantity);
                    existingLine.set_unit_price(price);
                    existingLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);
                    order.orderlines.remove(selectedLine);
                } else {
                    const xas_mayority_affect_orders = this.calculateAffectOrder(newQuantity, travelOption);
                    selectedLine.set_quantity(newQuantity);
                    selectedLine.set_unit_price(price);
                    selectedLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);
                }

                this.numberBuffer.capture();
                await order.apply_mayority_pricing();
                return true;
            } else {
                const palletPricePerBox = travelOption.xas_price_per_pallet;

                // Obtener cantidades existentes de otras líneas con el mismo producto, ID de MLA y MISMO estado de condición
                const existingPalletLine = order.orderlines.find(line => {
                    return line.product.id === product.id &&
                    line.getXasMlaId() === xasMlaId &&
                    line.get_unit_price() === palletPricePerBox &&
                    line.getXasSaleConditionState() === currentSaleCondition && // Añadido: verificar estado
                    line !== selectedLine;
                });
                const existingSurplusLine = order.orderlines.find(line => {
                    return line.product.id === product.id &&
                    line.getXasMlaId() === xasMlaId &&
                    line.get_unit_price() !== palletPricePerBox &&
                    line.getXasSaleConditionState() === currentSaleCondition && // Añadido: verificar estado
                    line !== selectedLine;
                });

                // Inicializar cantidades
                let existingPalletQuantity = existingPalletLine ? existingPalletLine.quantity : 0;
                let existingSurplusQuantity = existingSurplusLine ? existingSurplusLine.quantity : 0;

                // Calcular cantidad total
                let totalQuantity = existingPalletQuantity + existingSurplusQuantity + newQuantity;

                // Ajustar totalQuantity si excede la cantidad disponible
                if (totalQuantity > availableQty) {
                    totalQuantity = availableQty;
                }

                // Calcular pallets y sobrantes
                const pallets = Math.floor(totalQuantity / boxesPerPallet);
                const palletQuantity = pallets * boxesPerPallet;
                const surplusQuantity = totalQuantity - palletQuantity;

                // Actualizar o crear línea de pallets
                if (palletQuantity > 0) {

                    // Modificamos la linea de pallet existente
                    if (existingPalletLine) {
                        const xas_mayority_affect_orders = this.calculateAffectOrder(palletQuantity, travelOption);
                        existingPalletLine.set_quantity(palletQuantity);
                        existingPalletLine.set_unit_price(palletPricePerBox);
                        selectedLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);

                        // Si ya no hay cantidades sobrantes. La teoría dice que hemos modificado la linea sobrante, así que la borramos
                        if (surplusQuantity == 0){
                            order.orderlines.remove(selectedLine);
                            this.numberBuffer.reset();
                            await order.apply_mayority_pricing();
                            return true;
                        }

                    // Editamos la linea original para volvera una linea de pallets
                    } else {
                        let xas_mayority_affect_orders = this.calculateAffectOrder(palletQuantity, travelOption);
                        selectedLine.set_quantity(palletQuantity);
                        selectedLine.set_unit_price(palletPricePerBox);
                        selectedLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);

                        // Si nos sobran cantidades, las colocamos en una linea existente o generamos una linea nueva para las sobrantes
                        if (surplusQuantity > 0) {
                            xas_mayority_affect_orders = this.calculateAffectOrder(surplusQuantity, travelOption);
                            const surplusPrice = this.calculatePrice(surplusQuantity, travelOption);
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
                            this.numberBuffer.reset();
                            await order.apply_mayority_pricing();
                            return true;
                        }
                    }
                } else if (existingPalletLine) {
                    order.orderlines.remove(existingPalletLine);
                }

                // Actualizar o crear línea de sobrantes
                if (surplusQuantity > 0) {
                    const surplusPrice = this.calculatePrice(surplusQuantity, travelOption);
                    let xas_mayority_affect_orders = this.calculateAffectOrder(surplusQuantity, travelOption);
                    if (existingSurplusLine) {
                        existingSurplusLine.set_quantity(surplusQuantity);
                        existingSurplusLine.set_unit_price(surplusPrice);
                        existingSurplusLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);
                        order.orderlines.remove(selectedLine);
                    } else {
                        // Añadimos los cambios a la linea actual
                        selectedLine.set_quantity(surplusQuantity);
                        selectedLine.set_unit_price(surplusPrice);
                        selectedLine.setXasMayorityAffectOrders(xas_mayority_affect_orders);
                    }
                } else if (existingSurplusLine) {
                    order.orderlines.remove(existingSurplusLine);
                }

                this.numberBuffer.capture();
                await order.apply_mayority_pricing();
                return true;
            }
        }
    },
});