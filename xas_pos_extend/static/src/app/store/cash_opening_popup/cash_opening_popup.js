/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CashOpeningPopup } from "@point_of_sale/app/store/cash_opening_popup/cash_opening_popup";

// Guardamos la referencia al método original antes de parchearlo.
const _origSetup = CashOpeningPopup.prototype.setup;

patch(CashOpeningPopup.prototype, {
    setup(...args) {
        // Llamamos la implementación original
        _origSetup.call(this, ...args);

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

        // Texto: "Apertura de caja [Usuario] día [dd/mm/aaaa hh:mm:ss]"
        const dateStr = `${dd}/${mm}/${yyyy} ${hh}:${min}:${ss}`;
        this.state.notes = `Apertura de caja ${userName} día ${dateStr}`;
    },
    handleInputChange() {
        if (!this.env.utils.isValidFloat(this.state.openingCash)) {
            return;
        }
    }
});