# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

{
    'name': 'SMS Gateway',
    'category': 'Extra Tools',
    'version': '17.0.1.0',
    'license': 'OPL-1',
    'summary': 'This module allows to send SMS with multiple SMS Gateway in odoo.',
    'description': """
        SMS Gateway
    """,
    'images': ['static/description/banner.jpg'],
    'author': 'Kanak Infosystems LLP.',
    'website': 'http://www.kanakinfosystems.com',
    'depends': ['base_automation', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'data/sms_gateway_cron.xml',
        'data/sms_template_data.xml',
        'views/sms_gateway_views.xml',
        'views/sms_gateway_template_view.xml',
        'views/res_config_settings_views.xml',
        'views/sms_history_views.xml',
        'wizard/send_custom_sms_wizard_view.xml',
        'wizard/sms_gateway_composer_view.xml',
        'views/ir_actions_view.xml',
        'views/sms_marketing_views.xml',
        'views/sms_group_views.xml',
        'wizard/sms_marketing_schedule_date_views.xml',
        'views/res_users_view.xml'
    ],
    'installable': True,
    'price': 30,
    'currency': 'EUR',
}
