# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['bluemaxpay_card_present'] = {
            'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res

    def get_device_details(self):
        print('aaa', self)
        port = self.env['ir.config_parameter'].sudo(
        ).get_param('invoice_card_present.port')
        ip_address = self.env['ir.config_parameter'].sudo(
        ).get_param('invoice_card_present.ip_address')
        time_out = self.env['ir.config_parameter'].sudo(
        ).get_param('invoice_card_present.time_out')
        version_num = self.env['ir.config_parameter'].sudo(
        ).get_param('invoice_card_present.version_num')
        print(version_num)
        return {
            'port': port,
            'ip': ip_address,
            'time_out': time_out,
            'version_num': version_num
        }
