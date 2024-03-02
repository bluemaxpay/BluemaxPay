# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'SMSEagle SMS Gateway',
    'category': 'Extra Tools',
    'version': '17.0.1.0',
    'summary': 'SMSEagle SMS Gateway - User can able to send the sms via SMSEagle from any models like sale order, purchase order, invoice, etc. User can able to send the messages for marketing purpose also via Eagle',
    'description': """SMSEagle SMS Gateway""",
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://kanakinfosystems.com',
    'depends': ['sms_gateway_kanak'],
    'data': [
        'data/cron_data.xml',
        'data/smseagle_data.xml',
        'views/sms_gateway_smseagle_views.xml',
    ],
    'license': 'OPL-1',
    'application': True,
    'installable': True
}
