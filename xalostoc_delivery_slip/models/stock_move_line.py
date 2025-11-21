from collections import defaultdict
from odoo import models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"
    
    def _group_by_product(self):
        """ Returns a list of dictionaries that corresponds to a group of lines that share the same product.
        returns: 
            list [
                dictionary {
                    'product_name': product_id.name,
                    'product_uom': product_id.uom.name,
                    'move_lines': move_lines,
                    'qty_sum': sum of quantities,
                    'pieces': total of rows
                    },
                ...
                ]   
        """
        def get_dict_by_product(name, move_lines):
            return {
                'product_name': name, 
                'product_uom': move_lines[0].product_uom_id.name, 
                'move_lines': move_lines, 
                'qty_sum': sum(map(lambda _line: _line.quantity, move_lines)),
                'pieces': len(move_lines)
            }            
        result = defaultdict(list)
        for line in self:
            result[line.product_id.name].append(line)
        return [get_dict_by_product(name, move_lines) for name, move_lines in result.items()]
