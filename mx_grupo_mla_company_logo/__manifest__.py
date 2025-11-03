{
    'name': "Company Logo in NavBar",
    'description': """
        Agrega el logo de la empresa actual en la barra de navegación del backend.
        Compatible con Odoo 17.0
    """,
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Web',
    'version': '17.0.1.0.0',
    'depends': [
        'base',
        'web'
    ],
    'data': [
        # No necesitamos archivos de datos para este módulo
    ],
    'assets': {
        'web.assets_backend': [
            'mx_grupo_mla_company_logo/static/src/js/menu.js',
            'mx_grupo_mla_company_logo/static/src/css/menu.css',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}