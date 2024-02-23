{
    'name': 'BlueMax Pay Card Present: Payment',
    'version': '17.0.1.0',
    'category': 'Accounting/Accounting',
    'sequence': 20,
    'author': "BlueMax Pay",
    'summary': 'Payment Acquirer: BlueMax Pay Implementation',
    'description': """BlueMax Pay Payment Acquirer: Payment""",
    'depends': ['account', 'invoice_card_present'],
    'images': [],
    'data': [
            'security/ir.model.access.csv',
            'views/account_payment.xml',
            'wizard/bluemaxpay_payment.xml'
    ],
    'application': True,
    'license': 'LGPL-3',
}
