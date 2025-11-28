# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError
from datetime import date,datetime

class Destination(models.Model):
    _name = 'destination'
    _description = "Destino"

    name = fields.Char(
        string='Nombre',
    )