# -*- coding: utf-8 -*-
# ARCHIVO OPCIONAL: Agrega un campo de imágenes anotadas directamente en las tareas
# Para usar este archivo, descomenta el import en models/__init__.py

from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    image_annotation_ids = fields.One2many(
        'project.image.annotation', 
        'task_id', 
        string='Imágenes Anotadas'
    )
    image_annotation_count = fields.Integer(
        string='Número de Imágenes',
        compute='_compute_image_annotation_count'
    )

    @api.depends('image_annotation_ids')
    def _compute_image_annotation_count(self):
        for record in self:
            record.image_annotation_count = len(record.image_annotation_ids)

    def action_view_image_annotations(self):
        """Acción para ver las imágenes anotadas de la tarea"""
        self.ensure_one()
        return {
            'name': 'Imágenes Anotadas',
            'type': 'ir.actions.act_window',
            'res_model': 'project.image.annotation',
            'view_mode': 'kanban,tree,form',
            'domain': [('task_id', '=', self.id)],
            'context': {
                'default_task_id': self.id,
                'default_project_id': self.project_id.id,
            }
        }


class ProjectProject(models.Model):
    _inherit = 'project.project'

    image_annotation_ids = fields.One2many(
        'project.image.annotation', 
        'project_id', 
        string='Imágenes Anotadas'
    )
    image_annotation_count = fields.Integer(
        string='Número de Imágenes',
        compute='_compute_image_annotation_count'
    )

    @api.depends('image_annotation_ids')
    def _compute_image_annotation_count(self):
        for record in self:
            record.image_annotation_count = len(record.image_annotation_ids)

    def action_view_image_annotations(self):
        """Acción para ver las imágenes anotadas del proyecto"""
        self.ensure_one()
        return {
            'name': 'Imágenes Anotadas',
            'type': 'ir.actions.act_window',
            'res_model': 'project.image.annotation',
            'view_mode': 'kanban,tree,form',
            'domain': [('project_id', '=', self.id)],
            'context': {
                'default_project_id': self.id,
            }
        }
