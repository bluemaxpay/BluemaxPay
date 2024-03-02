# -*- coding: utf-8 -*-.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sms_gateway = fields.Many2one('sms.gateway', string='SMS Gateway', config_parameter='sms_gateway_kanak.sms_gateway', domain=[('state', 'in', ['test', 'enabled'])])
