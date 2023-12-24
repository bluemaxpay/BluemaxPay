{
    'name': 'BlueMax Pay Card Not Present',
    'version': '1.0',
    'category': 'Sales/Point Of Sale',
    'sequence': 20,
    'summary': 'Payment Acquirer: BlueMax Pay Implementation',
    'description': """BlueMax Pay Payment Acquirer""",
    'depends': ['point_of_sale'],
    'images': [],
    'data': [
            'security/ir.model.access.csv',
            'views/pos_payment_method.xml'
    ],
    'assets': {
        'point_of_sale.assets': [
            'pos_card_not_present/static/src/xml/BlueMaxPayOrderReceipt.xml',
            'pos_card_not_present/static/src/xml/bluemaxpay_popup.xml',
            'pos_card_not_present/static/src/js/ReprintReceiptButton.js',
            'pos_card_not_present/static/src/js/models.js',
            'pos_card_not_present/static/src/js/bluemaxpay_popup.js',
            'pos_card_not_present/static/src/js/BlueMaxPayOrderReceipt.js',
            'pos_card_not_present/static/src/js/payment_card_not_present.js',
        ],
        'web.assets_qweb': [
            'pos_card_not_present/static/src/xml/bluemaxpay_popup.xml',
            'pos_card_not_present/static/src/xml/BlueMaxPayOrderReceipt.xml',
        ],
    },
    'application': True,
    'license': 'LGPL-3',
}
