# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    "name": "Pos Customer Screen",
    "version": "16.0.2.0",
    "category": "website",
    "depends": ['point_of_sale'],
    'license': 'OPL-1',
    'website': 'https://www.kanakinfosystems.com',
    'author': 'Kanak Infosystems LLP.',
    'summary': 'Kanak Demo',
    "description": "kanak Website Demo",
    "data": [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/template.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    "auto_install": False,
    'assets': {
        'web.assets_frontend': [
            'pos_customer_screen/static/src/js/web/**',
            'pos_customer_screen/static/src/scss/custom.scss'
        ],
        'point_of_sale.assets': [
            'pos_customer_screen/static/src/js/pos/**',
            'pos_customer_screen/static/src/xml/**',
        ]
    },
    "installable": True,
}
