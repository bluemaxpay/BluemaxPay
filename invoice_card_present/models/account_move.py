# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    response_message = fields.Char('Response Message')
    response = fields.Text('Pax Terminal Response Invoice')
    bluemaxpay_process_card = fields.Boolean('BlueMax Pay')
    bluemaxpay_reference = fields.Char('BlueMax Pay Reference')
    terminal_id = fields.Integer('Terminal ID')
    response_amt = fields.Float('Pax Terminal Amount')
    
    def get_response_message(self, get_response_message, ResponseId, response, terminal_id, ResponseApproveAmt):
        self.response_message = get_response_message
        self.bluemaxpay_reference = ResponseId
        self.response = response
        self.terminal_id = terminal_id
        self.response_amt = ResponseApproveAmt

        print(get_response_message)
        return self
