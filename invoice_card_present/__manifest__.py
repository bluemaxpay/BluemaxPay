{
    'name': 'BlueMax Pay Card Present: Invoice',
    'version': '17.0.1.0',
    'category': 'Accounting/Accounting',
    'sequence': 20,
    'author': "BlueMax Pay",
    'summary': 'Payment Acquirer: BlueMax Pay Implementation',
    'description': """BlueMax Pay Payment Acquirer: Invoice""",
    'depends': ['sale', 'account'],
    'images': [],
    'data': [
        'data/account_payment_method_data.xml',
        'security/ir.model.access.csv',
        'views/pax_terminal_configuration.xml',
        'views/account_move.xml',
        'views/account_payment_register.xml',
        'views/res_config_settings_views.xml',
        'views/template.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'invoice_card_present/static/src/js/jquery_base64.js',
            'invoice_card_present/static/src/js/location_widget.js',
            'invoice_card_present/static/src/js/pax.js',
        ],
        'web.assets_frontend': [
            'invoice_card_present/static/src/js/location.js',
        ],
    },
    'application': True,
    'license': 'LGPL-3',
}
