{
    'name': 'BlueMax Pay Card Present: Invoice',
    'version': '1.0',
    'category': 'Accounting/Accounting',
    'sequence': 20,
    'summary': 'Payment Acquirer: BlueMax Pay Implementation',
    'description': """BlueMax Pay Payment Acquirer: Invoice""",
    'depends': ['sale', 'account'],
    'images': [],
    'data': [
        # 'data/account_payment_method_data.xml',
        'views/account_move.xml',
        'views/account_payment_register.xml',
        'views/res_config_settings_views.xml',
        'views/template.xml'
    ],
    'assets': {
        'web.assets_backend': [
            'invoice_card_present/static/src/js/*',

        ],
    },
    'application': True,
    'license': 'LGPL-3',
}
