# -*- coding: utf-8 -*-
{
    'name': 'POS Bluemax',
    'version': '16.0.1.0',
    'category': 'Sales/Point of Sale',
    'sequence': 6,
    'summary': 'Integrate your POS with a Bluemax',
    'description': 'POS Bluemax Pay',
    'data': [
        'security/ir.model.access.csv',
        'views/pos_payment_views.xml'
    ],
    'depends': ['point_of_sale','payment_bluemaxpay'],
    'installable': True,
    'assets': {
        'point_of_sale.assets': [
            'pos_bluemax/static/**/*',
        ],
    },
    'license': 'OPL-1',
}
