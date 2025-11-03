# -*- coding: utf-8 -*-
{
    'name': 'Project Image Annotations',
    'version': '17.0.1.0.5',
    'category': 'Project',
    'summary': 'Anotaciones interactivas en imágenes para proyectos de Odoo',
    'description': """
        Módulo de Anotaciones de Imágenes para Proyectos
        =================================================
        
        Este módulo permite:
        * Subir imágenes a proyectos y tareas
        * Hacer clic en puntos específicos de la imagen para agregar anotaciones
        * Marcar cada punto con un número y una flecha
        * Agregar descripción, secuencia y otros datos a cada anotación
        * Ver todas las anotaciones en una tabla
        * Gestionar el estado de cada anotación (pendiente, en proceso, completado)
        * Asignar responsables a cada anotación
        
        Características:
        ----------------
        * Widget interactivo para anotaciones visuales
        * Popup para agregar/editar información de anotaciones
        * Colores personalizables para cada anotación
        * Vista Kanban, Lista y Formulario
        * Integración completa con el módulo de Proyectos de Odoo
    """,
    'author': 'Tu Nombre',
    'website': 'https://www.tuempresa.com',
    'license': 'LGPL-3',
    'depends': [
        'project',
        'mail',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/project_image_annotation_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'project_image_annotation/static/src/css/image_annotation_widget.css',
            'project_image_annotation/static/src/js/image_annotation_widget.js',
            'project_image_annotation/static/src/xml/image_annotation_widget.xml',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
