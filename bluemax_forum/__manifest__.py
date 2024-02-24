# -*- coding: utf-8 -*-

{
    'name': 'Bluemax Forum',
    'version': '17.0.1.0',
    'category': 'Website/Website',
    'summary': 'Bluemax Forum',
    "description": "Bluemax Forum",
    'license': 'OPL-1',
    'depends': ['auth_signup', 'website_mail'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/views.xml',
        'views/menus_views.xml',
        'views/templates.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'bluemax_forum/static/src/scss/custom.scss',
            'bluemax_forum/static/src/js/custom.js',
        ]
    },
    'installable': True,
    'application': False,
    'auto_install': False
}
