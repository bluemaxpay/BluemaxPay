# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    is_bluemaxpay_card_present = fields.Boolean()
    response_message = fields.Char('Response Message')

    @api.onchange('payment_method_line_id')
    def _onchange_is_bluemaxpay_card_present(self):
        """change is_bluemaxpay_card_present"""
        if self.payment_method_line_id.code == 'bluemaxpay_card_present':
            self.is_bluemaxpay_card_present = True
        else:
            self.is_bluemaxpay_card_present = False

    def action_create_payments(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        print(active_ids, active_model, 'paid')
        account_move = self.env[active_model].browse(active_ids)
        if len(account_move) > 1:
            if len(account_move.mapped('partner_id')) > 1:
                raise ValueError(
                    "You can't process the group payment of different customer's invoices")
        res_list = []
        # for account_move in account_moves:
        if self.payment_method_line_id.code == 'bluemaxpay_card_present':
            bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                'name': self.communication,
                'reference': account_move.bluemaxpay_reference,
                'date': fields.Datetime.now(),
                'payment_type': 'capture',
                'move_id': account_move.id if len(account_move) == 1 else None,
                'move_ids': [(6, 0, account_move.ids)] if len(account_move) > 0 else None,
                'amount': self.amount,
                'card_id': self.card_id.id,
                'partner_id': account_move.partner_id.id,

            })
            transaction = self.env['payment.transaction'].create({
                'provider_id': self.env.ref(
                    'payment_bluemaxpay.payment_acquirer_bluemaxpay').id,
                'reference': self.communication,
                'provider_reference': bluemaxpay_trans.reference,
                'partner_id': self.partner_id.id,
                'invoice_ids': [(4, account_move.ids)],
                'amount': self.amount,
                'currency_id': self.currency_id.id,
                'state': 'draft',
                'bluemaxpay_trans_id': bluemaxpay_trans.id,
                'captured_amount': bluemaxpay_trans.captured_amount
            })
            bluemaxpay_trans.transaction_id = transaction.id
            if account_move.response_message != '000000':
                print(account_move.response_message, 'messsssage')
                account_move.response_message = ' '
                raise UserError("Can't process this payment")
            bluemaxpay_trans.state = 'post'
            bluemaxpay_trans.transaction = account_move.bluemaxpay_reference
            bluemaxpay_trans.reference = account_move.bluemaxpay_reference
            transaction._set_done()
            transaction._reconcile_after_done()
        res = super(AccountPaymentRegister, self).action_create_payments()
