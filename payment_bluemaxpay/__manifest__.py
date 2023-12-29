{
    'name': 'BlueMax Pay Payment',
    'version': '1.0',
    'category': 'Accounting/Payment Acquirers',
    'sequence': 20,
    'summary': 'Payment Acquirer: BlueMax Pay Implementation',
    'description': """BlueMax Pay Payment Acquirer""",
    'depends': ['base', 'payment', 'website_sale', 'sale_management', 'portal', 'invoice_card_present'],
    'images': ['static/description/banner.png'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_template.xml',
        'views/payment_provider.xml',
        'views/account_payment_register.xml',
        'views/bluemax_token.xml',
        'views/bluemaxpay_token.xml',
        'views/bluemaxpay_transaction.xml',
        'views/sale_order.xml',
        'views/sale_order_payment.xml',
        'views/sale_order_capture.xml',
        'views/res_partner.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'https://api2.heartlandportico.com/SecureSubmit.v1/token/gp-1.0.1/globalpayments.js',

        ],
        'web.assets_frontend': [
            'https://api2.heartlandportico.com/SecureSubmit.v1/token/gp-1.0.1/globalpayments.js',
            'payment_bluemaxpay/static/src/js/payment_form.js',
            'payment_bluemaxpay/static/src/js/payment_bluemaxpay.js'

        ],
    },
    'application': True,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
