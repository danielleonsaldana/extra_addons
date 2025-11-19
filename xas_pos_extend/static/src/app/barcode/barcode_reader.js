/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { BarcodeReader } from "@point_of_sale/app/barcode/barcode_reader_service";
import { ErrorBarcodePopup } from "@point_of_sale/app/barcode/error_popup/barcode_error_popup";

patch(BarcodeReader.prototype,{
    async _scan(code) {
        if (!code) {
            return;
        }
        if (code.startsWith("QR_ORDER|")) {
            const [prefix, pos_reference] = code.split("|");
            const cbMaps = this.exclusiveCbMap ? [this.exclusiveCbMap] : [...this.cbMaps];

            // Armamos un objeto parseBarcode para que los callbacks sepan de qué se trata
            const parseBarcode = {
                type: "qr_order",
                code: code,
                pos_reference: pos_reference,
            };
            const cbs = cbMaps.map((cbMap) => cbMap["qr_order"]).filter(Boolean);

            // Si no se encontró ningún callback para este tipo, mostramos un ErrorPopup
            if (cbs.length === 0) {
                this.popup.add(ErrorBarcodePopup, { code: code });
            }
            for (const cb of cbs) {
                await cb(parseBarcode);
            }
            return;
        }

        // Para cualquier otro código, llamamos al método original
        return super._scan(code);
    },
});