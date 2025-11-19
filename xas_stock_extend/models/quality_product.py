# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class QualityProduct(models.Model):
    _name = 'quality.product'
    _description = 'Calidad'

    name = fields.Char(string='Calidad', required=True)
    xas_code = fields.Char(string='Código', readonly=True, copy=False)
    xas_sequence_number = fields.Integer(string='Secuencia', readonly=True)
    xas_is_invailable = fields.Boolean(string='No aplicable a SKU', copy=False)

    _sql_constraints = [
        ('code_uniq', 'unique(xas_code)', 'El código debe ser único.')
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('xas_code'):
                next_seq = self._get_next_sequence_number()
                vals['xas_sequence_number'] = next_seq
                # Se indica la longitud deseada
                vals['xas_code'] = self._format_code(next_seq, 4)
        return super(QualityProduct, self).create(vals_list)

    def write(self, vals):
        if 'xas_code' in vals:
            raise ValidationError("El campo código no es editable.")
        return super(QualityProduct, self).write(vals)

    def _get_next_sequence_number(self):
        last_record = self.search([], order='xas_sequence_number desc', limit=1)
        if last_record:
            return last_record.xas_sequence_number + 1
        return 1

    def _format_code(self, seq, base_length):
        """
        Genera el código a partir del número de secuencia 'seq' y la longitud 'base_length'
        siguiendo este comportamiento:
          - Si seq <= (10^base_length - 1), se genera un código numérico de longitud fija (rellenado con ceros).
          - Una vez alcanzado el máximo numérico, se inicia una serie de etapas:
              Etapa 1: prefijo con (base_length - 1) dígitos "9" + 1 letra (de A a Z)
              Etapa 2: prefijo con (base_length - 2) dígitos "9" + 2 letras (de AA a ZZ)
              ...
              Etapa n: prefijo con (base_length - n) dígitos "9" + n letras
          Se continúa hasta generar el máximo, por ejemplo, "ZZZZ" para base_length = 4.
        """
        stage0_max = 10 ** base_length - 1
        if seq <= stage0_max:
            return str(seq).zfill(base_length)

        cumulative = stage0_max
        for i in range(1, base_length + 1):
            stage_count = 26 ** i
            if seq <= cumulative + stage_count:
                remainder = seq - cumulative
                letter_part = self._int_to_letters(remainder - 1, i)
                numeric_prefix = '9' * (base_length - i) if (base_length - i) > 0 else ''
                return numeric_prefix + letter_part
            cumulative += stage_count

        raise ValidationError("Se ha alcanzado el máximo de códigos disponibles.")

    def _int_to_letters(self, number, length):
        """
        Convierte un entero (number) a una cadena de 'length' caracteres en base 26,
        utilizando el alfabeto A-Z, donde 0 -> A, 1 -> B, ... 25 -> Z.
        """
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        result = ""
        for _ in range(length):
            result = letters[number % 26] + result
            number //= 26
        return result