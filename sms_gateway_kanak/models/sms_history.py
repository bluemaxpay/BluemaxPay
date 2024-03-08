# -*- coding: utf-8 -*-

from odoo import fields, models


class SMSHistory(models.Model):
    _name = 'sms.history'
    _description = 'SMS History'
    _rec_name = 'from_mobile'
    _order = 'id desc'

    sms_gateway = fields.Many2one('sms.gateway', string='SMS Gateway', required=True)
    partner_id = fields.Many2one('res.partner', string='Contact')
    from_mobile = fields.Char(string='From')
    to_mobile = fields.Char(string='To')
    date = fields.Datetime(default=lambda self: fields.Datetime.now())
    message = fields.Text(string='Message')
    sms_reference = fields.Char(string='SMS Reference')
    res_model = fields.Char('Related Document Model Name')
    res_id = fields.Many2oneReference('Related Document ID', help='Id of the followed resource', model_field='res_model')
    sms_marketing_id = fields.Many2one('sms.marketing', string='SMS Marketing')
    updated_date = fields.Datetime(default=lambda self: fields.Datetime.now())
    state = fields.Selection([('draft', 'Draft'), ('queued', 'Queued'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('undelivered', 'Undelivered'), ('failed', 'Failed')], default='draft')
    error_message = fields.Text('Error Message')
