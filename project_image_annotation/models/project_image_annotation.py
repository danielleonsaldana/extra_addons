# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ProjectImageAnnotation(models.Model):
    _name = 'project.image.annotation'
    _description = 'Anotaciones de Imágenes en Proyectos'
    _order = 'sequence, id'

    name = fields.Char(string='Nombre', required=True)
    project_id = fields.Many2one('project.project', string='Proyecto', required=True, ondelete='cascade')
    task_id = fields.Many2one('project.task', string='Tarea', ondelete='cascade')
    image = fields.Binary(string='Imagen', required=True, attachment=True)
    image_filename = fields.Char(string='Nombre del archivo')
    sequence = fields.Integer(string='Secuencia', default=10)
    annotation_ids = fields.One2many('project.image.annotation.point', 'annotation_id', string='Puntos de Anotación')
    annotation_count = fields.Integer(string='Número de Anotaciones', compute='_compute_annotation_count')

    @api.depends('annotation_ids')
    def _compute_annotation_count(self):
        for record in self:
            record.annotation_count = len(record.annotation_ids)


class ProjectImageAnnotationPoint(models.Model):
    _name = 'project.image.annotation.point'
    _description = 'Puntos de Anotación en Imagen'
    _order = 'numero, id'

    annotation_id = fields.Many2one('project.image.annotation', string='Anotación de Imagen', required=True, ondelete='cascade')
    numero = fields.Integer(string='Número', required=True)
    descripcion = fields.Text(string='Descripción', required=True)
    secuencia = fields.Integer(string='Secuencia', default=10)
    pos_x = fields.Float(string='Posición X (%)', required=True, digits=(5, 2))
    pos_y = fields.Float(string='Posición Y (%)', required=True, digits=(5, 2))
    color = fields.Char(string='Color', default='#FF0000')
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado'),
    ], string='Estado', default='pendiente')
    responsable_id = fields.Many2one('res.users', string='Responsable')
    fecha_creacion = fields.Datetime(string='Fecha de Creación', default=fields.Datetime.now)
    notas_adicionales = fields.Text(string='Notas Adicionales')

    _sql_constraints = [
        ('unique_numero_per_annotation', 'unique(annotation_id, numero)', 
         'El número debe ser único para cada imagen!')
    ]
