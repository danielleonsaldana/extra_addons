from odoo import api, fields, models

from datetime import datetime


class StockLot(models.Model):
    _inherit = "stock.lot"

    x_product_categ_id = fields.Many2one(
        'product.category',
        string="Categoría del producto",
        related='product_id.categ_id',
        store=True
    )
    
    additional_lot = fields.Char(string="Lot 2")
    move_line_ids = fields.One2many("stock.move.line", "lot_id")
    note = fields.Text()
    l10n_mx_edi_customs_number = fields.Char(compute="_compute_l10n_mx_edi_customs_number", store=True)
    l10n_mx_edi_customs_number_display = fields.Char(
        string="Customs Number",
        compute="_compute_l10n_mx_edi_customs_number",
        store=True,
    )
    l10n_mx_edi_customs_date = fields.Char(compute="_compute_l10n_mx_edi_customs_number", store=True)
    l10n_mx_edi_customs_date_display = fields.Date(
        string="Customs Date",
        compute="_compute_l10n_mx_edi_customs_number", 
        store=True,
    )
    lot_type_id = fields.Many2one("stock.lot.type")
    partner_id = fields.Many2one("res.partner")
    product_qty = fields.Float(store=True)

    @api.depends("delivery_ids", "move_line_ids.picking_id.stock_landed_cost_ids")
    def _compute_l10n_mx_edi_customs_number(self):
        for lot in self:
            landed_costs = lot.move_line_ids.picking_id.stock_landed_cost_ids
            lot.l10n_mx_edi_customs_number = ', '.join(landed_costs.mapped("l10n_mx_edi_customs_number"))
            lot.l10n_mx_edi_customs_number_display = lot.l10n_mx_edi_customs_number.split(", ")[-1]
            lot.l10n_mx_edi_customs_date = ', '.join([str(date) for date in set(landed_costs.mapped("date"))])
            last_date = lot.l10n_mx_edi_customs_date.split(", ")[-1]
            lot.l10n_mx_edi_customs_date_display = datetime.strptime(last_date, "%Y-%m-%d") if last_date != '' else False
