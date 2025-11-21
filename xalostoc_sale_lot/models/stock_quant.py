from odoo import models

class StockQuant(models.Model):
    _inherit = "stock.quant"
    
    def _gather(self, product_id, location_id, lot_id=None, package_id=None, owner_id=None, strict=False, qty=0):
        quants = super()._gather(product_id, location_id, lot_id, package_id, owner_id, strict, qty)
        sold_lots = self.env.context.get('sold_lots', [])
        if sold_lots:
            quants = quants.sorted(lambda q: q.lot_id in sold_lots, reverse=True)
        return quants
