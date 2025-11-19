/** @odoo-module **/

import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { patch } from "@web/core/utils/patch";

// Usamos el metodo original para evitar que se mande a llamar infinitamente
const _origGetInitialState = ClosePosPopup.prototype.getInitialState;

patch(ClosePosPopup.prototype, {
    getInitialState(...args) {
        // Llamamos al método original para obtener el state base
        const state = _origGetInitialState.call(this, ...args);

        // Obtenemos el nombre del cajero actual
        const userName = this.pos.get_cashier()?.name || "Usuario desconocido";

        // Formateamos la fecha/hora
        const now = new Date();
        const dd = String(now.getDate()).padStart(2, "0");
        const mm = String(now.getMonth() + 1).padStart(2, "0");
        const yyyy = now.getFullYear();
        const hh = String(now.getHours()).padStart(2, "0");
        const min = String(now.getMinutes()).padStart(2, "0");
        const ss = String(now.getSeconds()).padStart(2, "0");

        // "Cierre de caja [Nombre del Usuario] día [dd/mm/aaaa] [hh:mm:ss]"
        const dateStr = `${dd}/${mm}/${yyyy} ${hh}:${min}:${ss}`;
        state.notes = `Cierre de caja ${userName} día ${dateStr}`;

        return state;
    },
});
