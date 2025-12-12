# -*- coding: utf-8 -*-
{
    'name': 'Declaración IEPS',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Generación de archivo TXT para declaración de IEPS',
    'description': """
        Módulo para gestionar la declaración de IEPS:
        - Selección de facturas con IEPS
        - Generación de archivo TXT según formato SAT
        - Control de folios declarados
        - Prevención de duplicados
        - Tracking de declaraciones realizadas
    """,
    'author': 'Daniel León',
    'depends': [
        'account',
        'l10n_mx_edi',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/ieps_declaration_views.xml',
        'views/account_move_views.xml',
        'wizard/ieps_declaration_wizard_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
