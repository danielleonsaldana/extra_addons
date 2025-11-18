/** @odoo-module **/

import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { registry } from "@web/core/registry";
import { ListRenderer } from "@web/views/list/list_renderer";

export class DynamicColumnsOne2ManyRenderer extends ListRenderer {
    setup() {
        super.setup();
        // Aquí ya tienes las compañías en `this.props` o en otro lugar adecuado
        this.dynamicColumns = this.props.companies || ['Compañia 1','Compañia 2'];
        console.log("this", this);
        console.log("Dynamic Columns: ", this.dynamicColumns);
    }

    _renderHeader() {
        const $thead = super._renderHeader();
        const $tr = $thead.querySelector('tr');

        this.dynamicColumns.forEach(column => {
            const th = document.createElement('th');
            th.innerText = column.name;
            $tr.appendChild(th);
        });

        return $thead;
    }

    _renderRow(record) {
        const $tr = super._renderRow(record);

        this.dynamicColumns.forEach(() => {
            const td = document.createElement('td');
            td.innerText = '';  // Aquí puedes poner los datos que correspondan
            $tr.appendChild(td);
        });

        return $tr;
    }

    getActiveColumns(list) {
        console.log("list", list);
        var result = super.getActiveColumns(list);
        console.log("result", result);
        return result
    }
}

export class DynamicColumnsOne2ManyField extends X2ManyField {
    setup() {
        super.setup();
        // Pasamos las compañías como props para ser usadas en el renderer
        X2ManyField.components = { ListRenderer: DynamicColumnsOne2ManyRenderer };
    }
}

DynamicColumnsOne2ManyField.template = "DynamicColumnsOne2ManyWidget";

// Registrar el widget personalizado
registry.category("fields").add("dynamic_columns_one2many_widget", {
    ...x2ManyField,
    component: DynamicColumnsOne2ManyField,
});