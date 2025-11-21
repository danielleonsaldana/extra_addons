from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    additional_lot = fields.Char(related="lot_id.additional_lot", store=True, readonly=False)
    lot_type_id = fields.Many2one(related="lot_id.lot_type_id", store=True, readonly=False)

    def _create_and_assign_production_lot(self):
        # We need to store the values before they're set to False when the lot is created
        input_values = {line.id: (line.additional_lot, line.lot_type_id.id) for line in self}
        super()._create_and_assign_production_lot()
        for line in self:
            line.lot_id.additional_lot = input_values[line.id][0]
            line.lot_id.lot_type_id = input_values[line.id][1]
