{
    'name': 'BlueMax Pay Card Not Present',
    'version': '17.0.1.0',
    'category': 'Sales/Point Of Sale',
    'sequence': 20,
    'author': "BlueMax Pay",
    'summary': 'Payment Acquirer: BlueMax Pay Implementation',
    'description': """BlueMax Pay Payment Acquirer""",
    'depends': ['point_of_sale'],
    'images': [],
    'data': [
            'security/ir.model.access.csv',
            'views/pos_payment_method.xml'
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_card_not_present/static/src/js/models.js',
            'pos_card_not_present/static/src/xml/card_not_present_popup.xml',
            'pos_card_not_present/static/src/js/card_not_present_popup.js',
            'pos_card_not_present/static/src/js/payment_card_not_present.js',
            'pos_card_not_present/static/src/js/payment_saved_cards.js',
            'pos_card_not_present/static/src/js/saved_cards_popup.js',
            'pos_card_not_present/static/src/xml/saved_cards_popup.xml',
            'pos_card_not_present/static/src/js/BlueMaxPayOrderReceipt.js',
            'pos_card_not_present/static/src/xml/BlueMaxPayOrderReceipt.xml',
            'pos_card_not_present/static/src/js/ReprintReceiptButton.js',
        ],
    },
    'application': True,
    'license': 'LGPL-3',
}
