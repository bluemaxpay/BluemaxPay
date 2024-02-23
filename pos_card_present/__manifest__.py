{
    'name': 'BlueMax Pay Card Present',
    'version': '17.0.1.0',
    'category': 'Sales/Point Of Sale',
    'sequence': 20,
    'author': "BlueMax Pay",
    'summary': 'Payment Acquirer: BlueMax Pay Implementation',
    'description': """BlueMax Pay Payment Acquirer""",
    'depends': ['point_of_sale'],
    'images': [],
    'data': [
            'views/pos_payment_method.xml',
            'views/pos_payment.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_card_present/static/src/js/models.js',
            'pos_card_present/static/src/js/payment_card_present.js',
            'pos_card_present/static/src/js/pax.js',
            'pos_card_present/static/src/js/jquery_base64.js',
        ],
    },
    'application': True,
    'license': 'LGPL-3',
}
