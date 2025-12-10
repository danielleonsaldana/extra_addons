# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import date,datetime
import logging
_logger = logging.getLogger(__name__)


class TrackingCostLine(models.Model):
    _inherit = 'tracking.cost.line'  # Ajusta según el nombre real de tu modelo
    
    def write(self, vals):
        """
        Sobrescribir write para recalcular las líneas de compra cuando cambien los incrementables
        """
        result = super(TrackingCostLine, self).write(vals)
        
        # Si cambió algún campo que afecta el total
        if any(field in vals for field in ['xas_amount', 'xas_total_amount', 'xas_exchange_usd_mxn']):
            # Recalcular el total de incrementables del tracking
            for line in self:
                if line.xas_tracking_id:
                    line.xas_tracking_id._compute_total_incrementables_mxn()
                    # Forzar recálculo de las líneas de compra
                    line.xas_tracking_id.xas_purchase_order_line_ids._compute_amounts_custom()
        
        return result
    
    @api.model_create_multi
    def create(self, vals_list):
        """
        Sobrescribir create para recalcular cuando se creen nuevas líneas
        """
        lines = super(TrackingCostLine, self).create(vals_list)
        
        # Recalcular para todos los trackings afectados
        trackings = lines.mapped('xas_tracking_id')
        for tracking in trackings:
            tracking._compute_total_incrementables_mxn()
            tracking.xas_purchase_order_line_ids._compute_amounts_custom()
        
        return lines
    
    def unlink(self):
        """
        Sobrescribir unlink para recalcular cuando se eliminen líneas
        """
        trackings = self.mapped('xas_tracking_id')
        result = super(TrackingCostLine, self).unlink()
        
        # Recalcular después de eliminar
        for tracking in trackings:
            if tracking.exists():
                tracking._compute_total_incrementables_mxn()
                tracking.xas_purchase_order_line_ids._compute_amounts_custom()
        
        return result