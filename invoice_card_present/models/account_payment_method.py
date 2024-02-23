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

    def get_device_details(self, terminal_id=None):
        print('aaa', self)
        pax_config = self.env['pax.terminal.configuration'].search(
            [('id', '=', terminal_id)], limit=1)

        port = pax_config.port
        ip_address = pax_config.ip_address
        time_out = pax_config.time_out
        version_num = pax_config.version_num
        print(version_num)
        return {
            'port': port,
            'ip': ip_address,
            'time_out': time_out,
            'version_num': version_num
        }
