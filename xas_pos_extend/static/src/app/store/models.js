/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Orderline } from "@point_of_sale/app/store/models";
import { Order} from "@point_of_sale/app/store/models";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

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

patch(Orderline.prototype, {

    setup(_defaultObj, options){
        this.xas_sale_condition_state_id = this.xas_sale_condition_state_id || "";
        this.xas_sale_condition_state_name = this.xas_sale_condition_state_name || "";
        this.xas_trip_number == this.xas_trip_number || "";
        this.xas_product_pricelist_mla_id == this.xas_product_pricelist_mla_id || "";
        this.xas_stock_lot_id == this.xas_stock_lot_id || "";
        this.xas_stock_lot_name == this.xas_stock_lot_name || "";
        this.xas_mayority_affect_orders == this.xas_mayority_affect_orders || "";
        super.setup(...arguments);
    },

    init_from_JSON(json) {
        super.init_from_JSON(json);
        this.setXasSaleConditionState(json.xas_sale_condition_state_id);
        this.setXasSaleConditionStateName(json.xas_sale_condition_state_name);
        this.setXasTripNumber(json.xas_trip_number);
        this.setXasMlaId(json.xas_product_pricelist_mla_id);
        this.setXasStockLotId(json.xas_stock_lot_id);
        this.setXasStockLotName(json.xas_stock_lot_name);
        this.setXasMayorityAffectOrders(json.xas_mayority_affect_orders);
    },

    getXasTripNumber() {
        return this.xas_trip_number;
    },
    getXasMlaId() {
        return this.xas_product_pricelist_mla_id;
    },
    getXasSaleConditionState() {
        return this.xas_sale_condition_state_id;
    },
    getXasSaleConditionStateName() {
        return this.xas_sale_condition_state_name;
    },
    getXasStockLotId() {
        return this.xas_stock_lot_id;
    },
    getXasStockLotName() {
        return this.xas_stock_lot_name;
    },
    getXasMayorityAffectOrders(){
        return this.xas_mayority_affect_orders;
    },

    setXasTripNumber(xas_trip_number) {
        this.xas_trip_number = xas_trip_number;
    },
    setXasMlaId(xas_product_pricelist_mla_id) {
        this.xas_product_pricelist_mla_id = xas_product_pricelist_mla_id;
    },
    setXasSaleConditionState(xas_sale_condition_state_id) {
        this.xas_sale_condition_state_id = xas_sale_condition_state_id;
    },
    setXasSaleConditionStateName(xas_sale_condition_state_name) {
        this.xas_sale_condition_state_name = xas_sale_condition_state_name;
    },
    setXasStockLotId(xas_stock_lot_id) {
        this.xas_stock_lot_id = xas_stock_lot_id;
    },
    setXasStockLotName(xas_stock_lot_name) {
        this.xas_stock_lot_name = xas_stock_lot_name;
    },
    setXasMayorityAffectOrders(xas_mayority_affect_orders){
        this.xas_mayority_affect_orders = xas_mayority_affect_orders;
    },

    export_as_JSON() {
        let result = super.export_as_JSON();
        result['xas_sale_condition_state_id'] = this.getXasSaleConditionState();
        result['xas_sale_condition_state_name'] = this.getXasSaleConditionStateName();
        result['xas_trip_number'] = this.getXasTripNumber();
        result['xas_product_pricelist_mla_id'] = this.getXasMlaId();
        result['xas_stock_lot_id'] = this.getXasStockLotId();
        result['xas_stock_lot_name'] = this.getXasStockLotName();
        result['xas_mayority_affect_orders'] = this.getXasMayorityAffectOrders();
        return result;
    },

    getDisplayData(){
        let data = super.getDisplayData();
        data['xas_trip_number'] = this.getXasTripNumber();
        data['xas_sale_condition_state_name'] = this.getXasSaleConditionStateName();
        data['xas_stock_lot_name'] = this.getXasStockLotName();
        return data;
    }
});

patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.xas_saler_id = this.xas_saler_id || "";
        this.xas_cashier_id = this.xas_cashier_id || "";
        this.xas_is_invoiceable = this.xas_is_invoiceable || false;
        this.xas_mark_as_paid = this.xas_mark_as_paid || false;

        // Verificar si no hay cliente asignado y establecer el cliente predeterminado de pos.config
        if (!this.partner) {
            const defaultCustomerId = this.pos.config.xas_default_pos_client_id;
            if (defaultCustomerId) {
                const defaultClient = this.pos.db.get_partner_by_id(defaultCustomerId[0]);
                if (defaultClient) {
                    this.set_partner(defaultClient);
                }
            }
        }
    },

    get_xas_is_invoiceable() {
        return this.xas_is_invoiceable;
    },
    get_xas_mark_as_paid() {
        return this.xas_mark_as_paid;
    },

    init_from_JSON(json) {
        super.init_from_JSON(json);
        // Precargar xas_saler_id y xas_cashier_id
        if (json.xas_saler_id) {
            this.xas_saler_id = json.xas_saler_id;
        }
        if (json.xas_cashier_id) {
            this.xas_cashier_id = json.xas_cashier_id;
        }
        this.xas_is_invoiceable = json.xas_is_invoiceable || false;
        /*Validamos que se cuente con id de la orden para ejecutar el metodo*/
        if (json.server_id){
            json.xas_mark_as_paid = this._get_xas_mark_as_paid(json.server_id)
        }else{
            json.xas_mark_as_paid = this.xas_mark_as_paid || false;
        }
    },

    // Agregamos nuestros campos custom a la orden de venta
    export_as_JSON() {
        const json = super.export_as_JSON();
        // Credito
        const paymentLines = this.get_paymentlines() || [];
        const usedCredit = paymentLines.some((line) =>
            line.payment_method?.type === "pay_later"
        );
        json.xas_is_credit = usedCredit ? true : false;

        // Vendedor o cajero
        const currentEmployeeId = this.cashier?.id;
        if (this.pos.config.xas_pos_role === 'for_saler') {
            json.xas_saler_id = currentEmployeeId || false;
            json.xas_cashier_id = this.xas_cashier_id;
        } else if (this.pos.config.xas_pos_role === 'for_cashier') {
            json.xas_saler_id = this.xas_saler_id;
            json.xas_cashier_id = currentEmployeeId || false;
        }
        json.xas_is_invoiceable = this.xas_is_invoiceable || false;
        /*json.xas_mark_as_paid = this.xas_mark_as_paid || false;*/

        return json;
    },

    async _get_xas_mark_as_paid(order_id) {
        const xas_mark_as_paid = await (this.orm || this.pos.orm).call("pos.order", "get_pos_order_data", [[order_id], order_id]);
        return xas_mark_as_paid
    },

    // Eliminamos la funcionalidad nativa de las listas de precios para evitar el planchado de precios
    set_pricelist(pricelist) {
    },

    // Añadimos el campo es facturable a la orden
    set_xas_is_invoiceable(xas_is_invoiceable) {
        this.assert_editable();
        this.xas_is_invoiceable = xas_is_invoiceable;
    },
    set_xas_mark_as_paid(xas_mark_as_paid) {
        this.assert_editable();
        this.xas_mark_as_paid = xas_mark_as_paid;
    },

    // Detectamos si se esta pagando con credito y enviamos un mensaje en caso de ser así
    add_paymentline(payment_method) {
        if (payment_method.type === "pay_later") {
            this.pos.popup.add(ErrorPopup, {
                title: 'La compra usa crédito',
                body: 'Su compra estará sujeta a aprobación para poder ser realizada',
            });
        }
        return super.add_paymentline(payment_method);
    },

    /**
     * Revisa si **cualquier** línea (sin condición de venta) tiene
     * xas_mayority_affect_orders como verdadero
     * Si es así, ajusta los precios de TODAS las líneas (que tampoco
     * tengan condición) al precio de mayoreo; en caso contrario,
     * los devuelve al precio menudista.
    */
    async apply_mayority_pricing() {
        const companyId    = this.pos.company.id;
        const hasMayoreo   = this.orderlines.some(
            (l) => l.getXasMayorityAffectOrders() && !l.getXasSaleConditionState()
        );
        const changes = [];

        for (const line of this.orderlines) {
            if (line.getXasSaleConditionState()) {
                continue;
            }
            const mlaId = line.getXasMlaId();

            // Llamada al servidor (async / await)
            const productId  = line.product.id;
            const updatedPricelists = await (this.orm || this.pos.orm).call(
                "product.product",
                "sync_mla_pricelists",
                [[productId], companyId]
            );

            const pl = (updatedPricelists || []).find(
                (pl) => pl.xas_mla_id === mlaId
            );
            if (!pl) {
                console.log('Algo salio mal');
                continue;
            }

            // ---------- Datos del servidor ----------
            const qtyAvail     = pl.xas_available_qty;
            const boxesPal     = pl.xas_boxes_by_pallet;
            const pricePallet  = pl.xas_price_per_pallet;
            const priceMenudeo = pl.xas_price_per_box;
            const priceMayoreo = pl.xas_mayority_price;
            // ---------- Situación de la línea ----------
            const qtyLine      = line.get_quantity();
            const priceLine    = Number(line.get_unit_price());

            let expectedPrice;
            if (boxesPal > 0 && qtyLine >= boxesPal) {
                expectedPrice = pricePallet;
            } else if (hasMayoreo) {
                expectedPrice = priceMayoreo;
            } else {
                expectedPrice = priceMenudeo;
            }

            const priceMismatch = priceLine !== Number(expectedPrice);
            const qtyMismatch   = qtyLine > qtyAvail;

            if (!(priceMismatch || qtyMismatch)) {
                continue;
            }

            // -------------- Aplicar correcciones --------------
            let removed = false;
            if (priceMismatch) {
                line.set_unit_price(expectedPrice);
            }
            if (qtyMismatch) {
                if (qtyAvail > 0) {
                    line.set_quantity(qtyAvail);
                } else {
                    this.orderlines.remove(line);   // sin stock ⇒ eliminar
                    removed = true;
                }
            }

            changes.push({
                name: line.product.display_name,
                priceChanged: priceMismatch ? { from: priceLine, to: expectedPrice } : null,
                qtyChanged:   qtyMismatch   ? { from: qtyLine,  to: qtyAvail      } : null,
                removed,
            });
        }
        return changes;
    },

    // Actualizar los precios en tiempo real
    async _recompute_prices_in_real_time() {
        const diffs = await this.apply_mayority_pricing();
        if (!diffs.length) {
            return;
        }

        await loadSweetAlert2();

        const listHtml = diffs.map(d => {
            if (d.removed) {
                return `
                    <li>
                        <b>${d.name}</b>: línea eliminada (sin stock)
                    </li>`;
            }
            const changes = [];
            if (d.priceChanged) {
                changes.push(
                    `Precio ${d.priceChanged.from} → <b>${d.priceChanged.to}</b>`
                );
            }
            if (d.qtyChanged) {
                changes.push(
                    `Cantidad ${d.qtyChanged.from} → <b>${d.qtyChanged.to}</b>`
                );
            }
            return `
                <li>
                    <b>${d.name}</b>: ${changes.join(" · ")}
                </li>`;
        }).join("");

        Swal.fire({
            icon: "info",
            title: "Se ajustaron precios/cantidades",
            html: `<ul style="text-align:left;line-height:1.4">${listHtml}</ul>`,
            confirmButtonText: "Aceptar",
            width: 600,
        });
    },

    // Sobrescribimos el método pay para evitar que se muestre el ConfirmPopup
    async pay() {
        if (!this.canPay()) {
            return;
        }
        await this._recompute_prices_in_real_time();

        this.pos.mobile_pane = "right";
        this.env.services.pos.showScreen("PaymentScreen");
        return true;
    }
});