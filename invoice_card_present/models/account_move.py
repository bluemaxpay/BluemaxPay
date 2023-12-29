# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    response_message = fields.Char('Response Message')
    bluemaxpay_process_card = fields.Boolean('BlueMax Pay')
    bluemaxpay_reference = fields.Char('BlueMax Pay Reference')

    def get_response_message(self, get_response_message, ResponseId):
        self.response_message = get_response_message
        self.bluemaxpay_reference = ResponseId
        print(get_response_message)
        return self
