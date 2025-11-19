/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";

patch(ProductsWidget.prototype, {
    get productsToDisplay() {
        // Si el usuario no buscó nada, devolvemos tal cual
        const standardList = super.productsToDisplay;
        if (!this.searchWord) {
            return standardList;
        }

        // Obtenemos **todos** los productos cargados en el POS
        // En caso de romperse por falta de categorias usar const allProducts = Object.values(this.pos.db.product_by_id);
        const allProducts = this.pos.db.get_product_by_category(0);

        // Filtramos por 'xas_trip_number_name' en mla_pricelists
        const tripMatches = allProducts.filter((product) => {
            if (!product.mla_pricelists) return false;
            return product.mla_pricelists.some(mla =>
                (mla.xas_trip_number_name || "").includes(this.searchWord)
            );
        });

        // Unimos la lista estándar con los que matchean por trip_number
        const combinedSet = new Set([...standardList, ...tripMatches]);
        const combinedArray = Array.from(combinedSet);
        // Retornamos alfabéticamente
        return combinedArray.sort((a, b) => a.display_name.localeCompare(b.display_name));
    },

    async loadProductFromDB() {
        const { searchProductWord } = this.pos;
        if (!searchProductWord) {
            return;
        }
        const cleanedProductWord = searchProductWord.replace(/;product_tmpl_id:\d+$/, '');
        const domain = [
            "|",
            "|",
            ["name", "ilike", cleanedProductWord],
            ["default_code", "ilike", cleanedProductWord],
            ["barcode", "ilike", cleanedProductWord],
            ["available_in_pos", "=", true],
            ["sale_ok", "=", true],
        ];

        const { limit_categories, iface_available_categ_ids } = this.pos.config;
        if (limit_categories && iface_available_categ_ids.length > 0) {
            domain.push(["pos_categ_ids", "in", iface_available_categ_ids]);
        }

        try {
            const limit = 30;
            const ProductIds = await this.orm.call(
                "product.product",
                "search",
                [
                    [
                        "&",
                        ["available_in_pos", "=", true],
                        "|",
                        "|",
                        ["name", "ilike", searchProductWord],
                        ["default_code", "ilike", searchProductWord],
                        ["barcode", "ilike", searchProductWord],
                        ["xas_available_pos_product_by_qty_and_price", "=", true],
                    ],
                ],
                {
                    offset: this.state.currentOffset,
                    limit: limit,
                }
            );
            if (ProductIds.length) {
                await this.pos._addProducts(ProductIds, false);
            }
            this.updateProductList();
            return ProductIds;
        } catch (error) {
            if (error instanceof ConnectionLostError || error instanceof ConnectionAbortedError) {
                return this.popup.add(OfflineErrorPopup, {
                    title: _t("Network Error"),
                    body: _t(
                        "Product is not loaded. Tried loading the product from the server but there is a network error."
                    ),
                });
            } else {
                throw error;
            }
        }
    }
});