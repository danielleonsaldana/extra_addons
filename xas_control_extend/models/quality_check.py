from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError, RedirectWarning

class QualityCheck(models.Model):
    _inherit = 'quality.check'

    # xas_quality_check_id = fields.Many2one('quality.check', string="Quality Check", required=True)
    xas_invoice_ids = fields.Many2many('account.move', string="Factura", related="picking_id.purchase_id.invoice_ids", readonly=True)
    xas_transport = fields.Many2one('tracking.routes', string='Transporte', related="xas_tracking_id.xas_tracking_route_id", readonly=False, store=True)
    xas_reception_date = fields.Datetime(string='Fecha de Recepción', related="picking_id.date_done", help='Fecha de recepción', )
    xas_responsible_id = fields.Many2one('res.users', string='Responsable', required=True, default=lambda self:self.env.user.id)
    xas_container = fields.Char(string='Contenedor', required=False, related="xas_tracking_id.xas_container" , readonly=False, store=True)
    xas_is_claim = fields.Boolean(string='¿Es Reclamo?')
    xas_product_ids = fields.One2many('product.detail', 'xas_quality_check_id', string="Products")
    xas_tracking_id = fields.Many2one('tracking', string='Id de seguimiento', copy=False, related="picking_id.xas_tracking_id", store=True)
    xas_trip_number_id = fields.Many2one('trip.number', related='xas_tracking_id.xas_trip_number', string='Código de embarque', copy=False, store=True)
    picking_ids = fields.Many2many('stock.picking',string='Movimientos',)

    quality_state = fields.Selection(selection_add=[('to_process', 'A procesar'), ('in_process', 'En proceso'), ('pass',), ('sent', 'Enviado'), ('fail',)])

    xas_picking_count = fields.Integer(
        string="Movimientos",
        compute="_compute_xas_picking_count",
        store=False
    )

    @api.depends('xas_product_ids')
    def _compute_xas_picking_count(self):
        for record in self:
            # Filtrar los pickings relacionados a este registro
            pickings = self.env['stock.picking'].search([('origin', '=', record.name)])
            record.xas_picking_count = len(pickings)

    def action_view_xas_pickings(self):
        self.ensure_one()
        # Filtrar los pickings relacionados al registro actual
        pickings = self.env['stock.picking'].search([('origin', '=', self.name)])
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('id', 'in', pickings.ids)]
        return action

    @api.model_create_multi
    def create(self, vals):
        result = super(QualityCheck, self).create(vals)
        for rec in result:
            # Si existe un picking asociado
            if rec.picking_id.id:
                lines = []
                # Cargamos las lineas de acuerdo a los moves del picking
                for move_id in rec.picking_id.move_ids_without_package:
                    lines.append((0,0,{
                        'xas_move_id':move_id.id,
                        'xas_product_id':move_id.product_id,
                    }))
                if lines != []:
                    rec.write({'xas_product_ids':lines})

        return result

    def start_inspection(self):
        self.ensure_one()

        # Verificar que haya valores en 'xas_samples' mayores a 0
        if not any(sample > 0 for sample in self.xas_product_ids.mapped('xas_samples')):
            raise ValidationError("No se establecieron valores en muestras. Por favor, verifica los datos.")

        # Verificar que las ubicaciones estén configuradas
        if not self.company_id.xas_location_out_id.id or not self.company_id.xas_location_in_id.id:
            raise ValidationError("Las ubicaciones de origen y destino no están configuradas en la compañía.")

        # Crear las líneas de movimiento
        move_lines = []
        for line in self.xas_product_ids:
            if line.xas_samples > 0:
                move_lines.append((0, 0, {
                    'product_id': line.xas_product_id.id,
                    'product_uom_qty': line.xas_samples,
                    'product_uom': line.xas_product_id.uom_id.id,
                    'name': line.xas_product_id.name,
                    'location_id': self.company_id.xas_location_out_id.id,
                    'location_dest_id': self.company_id.xas_location_in_id.id,
                }))
        if not move_lines:
            raise ValidationError("No hay productos con cantidades válidas para transferir.")

        internal_picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),  # Filtra los tipos de picking internos
            ('company_id', '=', self.company_id.id)  # Coincide con la compañía del registro actual
        ], limit=1)  # Obtiene solo el primero encontrado

        if not internal_picking_type:
            raise UserError("No se encontró un tipo de picking 'Interno' para esta compañía.")

        # Crear la transferencia interna
        picking = self.env['stock.picking'].create({
            'state': 'draft',
            'company_id': self.company_id.id,
            'partner_id': False,
            'location_id': self.company_id.xas_location_out_id.id,
            'location_dest_id': self.company_id.xas_location_in_id.id,
            'picking_type_id': internal_picking_type.id,
            'origin': self.name,
            'move_ids_without_package':move_lines
            # 'move_type': 'direct',  # Transferencia directa
        })

        # Confirmar y procesar la transferencia
        # picking.action_confirm()
        # picking.action_assign()
        # picking.button_validate()

        # Agregamos el picking al record
        self.write({'picking_ids':[(6,0,picking.ids)], 'quality_state':'to_process'})

        # Creamos las lineas de product_detail_line
        for line in self.xas_product_ids:
            line.do_lines()

        return True

    def send_email(self):
        self.ensure_one()  # Asegurarse de que solo se está procesando un registro

        # Preparar valores para el asistente de enviar correos
        template_id = self.env.ref('xas_control_extend.mail_template_quality_check_notification').id  # Usa una plantilla existente o crea una nueva
        ctx = {
            'default_model': self._name,
            # 'default_res_ids': self.ids,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            # 'default_partner_ids': [self.xas_partner_custom_id.id],
        }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Enviar correo',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'context': ctx,
            'target': 'new',
        }

    def action_send_email(self):
        for record in self:
            template.send_mail(record.id, force_send=True)  # Envía el correo
            record.write({'xas_state': 'sent'})  # Cambia el estado

class ProductDetail(models.Model):
    _name = 'product.detail'
    _description = 'Detalle de los productos'

    name = fields.Char('Nombre')
    xas_quality_check_id = fields.Many2one('quality.check', string="Control de calidad id")  # Relación con quality.check
    xas_move_id = fields.Many2one('stock.move', string='Id movimiento',)
    xas_product_id = fields.Many2one('product.product', string='Producto', related="xas_move_id.product_id")  # Relación con el producto
    xas_boxes = fields.Integer(string="Cajas", related="xas_move_id.xas_real_box")
    xas_samples = fields.Integer(string="Muestras")
    xas_responsible = fields.Many2one('res.users', string='Responsable', related="xas_quality_check_id.xas_responsible_id")
    xas_status = fields.Selection([
        ('pending', 'Pendiente'),
        ('in_progress', 'Proceso'),
        ('completed', 'Hecho')
    ], string="Status")
    xas_end_date = fields.Date(string="End Date")
    xas_product_detail_line_ids = fields.One2many(
        string='Revision de cajas',
        comodel_name='product.detail.line',
        inverse_name='xas_product_detail_id',
    )

    xas_detail_defect_id = fields.One2many(
        string='Linea de defecto',
        comodel_name='detail.defect',
        inverse_name='xas_detail_id',
    )

    xas_note = fields.Text(string='Otras notas')

    def open_quality_check_form(self):
        self.ensure_one()  # Asegura que solo se ejecute con un solo registro de product.detail
        return {
                'type': 'ir.actions.act_window',
                'name': 'Inspección',
                'res_model': 'product.detail',
                'view_mode': 'form',
                'res_id': self.id,
                # 'target': 'new',
            }

    # def do_lines(self):
    #     lines_list = []
    #     limit = self.xas_samples
    #     lines_dict = []
    #     for i in range(1, limit + 1):  # Empieza en 1 y termina en el límite
    #         lines_dict.append((0,0,{'name':str(self.xas_product_id.name) + ' NO. '+ str(i),'display_type':'line_section'})) # Agregamos la sección
    #         # Se crean las lineas de acuerdo a las carcteristicas relacionadas
    #         for char_id in self.xas_product_id.xas_product_custom_mla_id.characteristics_ids:
    #             lines_dict.append((0,0,{'xas_characteristic_id':char_id.id,}))
    #     self.write({"xas_product_detail_line_ids":lines_dict})

    def do_lines(self):
        # Si ya hay lineas
        if self.xas_product_detail_line_ids.ids != []:
             # Limpiamos lineas
            self.write({"xas_product_detail_line_ids": False})

        lines_dict = []
        # Crear una única línea de tipo sección
        lines_dict.append((0, 0, {
            'name': f"{self.xas_product_id.name}",
            'display_type': 'line_section',
        }))

        for char_id in self.xas_product_id.xas_product_custom_mla_id.characteristics_ids:
            lines_dict.append((0, 0, {
                'xas_characteristic_id': char_id.id,
            }))

        # Actualizar el campo One2many con las líneas generadas
        self.write({"xas_product_detail_line_ids": lines_dict})

class ProductDetailLine(models.Model):
    _name = 'product.detail.line'
    _description = 'linea de detalle de los productos'
    _order="sequence"

    xas_product_detail_id = fields.Many2one(
        'product.detail',
        string='ID  detalle de producto',
    )
    name = fields.Char(
        string='Nombre',
    )
    sequence = fields.Integer(string="Secuencia")
    display_type = fields.Selection(
        selection=[
            ('line_section', "Sección"),
            ('line_note', "Nota"),
        ],
        default=False)
    xas_characteristic_id = fields.Many2one('product.custom.mla.characteristic', string='Característica')
    xas_data = fields.Char(string='Dato')
    xas_attachment = fields.Binary(string="Evidencia fotográfica")  # Campo para adjuntar archivos
    xas_attachment_name = fields.Char(string="Nombre del archivo")  # Para guardar el nombre del archivo
    xas_note = fields.Char(string='Nota adicional:')

    xas_detail_defect_ids = fields.One2many(
        string='Linea de defecto',
        comodel_name='detail.defect',
        inverse_name='xas_detail_id',
    )

    xas_image_ids = fields.Many2many(
        'ir.attachment',
        string="Imagenes",
        domain="[('mimetype', 'ilike', 'image/')]",
        help="Sube multiples imagenes"
    )

class DetailDefect(models.Model):
    _name = 'detail.defect'
    _description = 'Linea de defecto'

    xas_detail_id = fields.Many2one(string='Id de detalle',comodel_name='product.detail',)

class Defect(models.Model):
    _name = 'defect'
    _description = 'Defecto'

    name = fields.Char(
        string='Nombre',
    )
