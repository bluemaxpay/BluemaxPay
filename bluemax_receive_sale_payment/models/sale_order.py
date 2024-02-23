from odoo import models, fields, api
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_id = fields.Many2one('account.payment', 'Sale Order')
    payment_amt = fields.Float(string="Payment Amount", compute='_get_payment_amount')

    def _get_payment_count(self):
        for record in self:
            record.payment_count = self.env['account.payment'].search_count([('sale_id', '=', record.id)])

    def action_view_payments(self):
        action = self.env.ref('account.action_account_payments').read([])[0]
        payments = self.env['account.payment'].search([('sale_id', '=', self.id)])
        action['domain'] = [('id', 'in', payments.ids)]
        return action

    def _get_payment_amount(self):
        for record in self:
            payment_amt = 0.0
            if self.user_has_groups('account.group_account_invoice'):
                data = self.env['account.payment'].read_group([('sale_id', '=', record.id)], ['sale_id', 'amount'], ['sale_id'])
                for d in data:
                    payment_amt += d['amount']
            record.payment_amt = payment_amt

    def create_payment(self):
        manual_paid = self.env['account.payment'].search(
            [('state', 'in', ['posted']), ('sale_id', '=', self.id)])

        # amount_manual = sum(manual_paid.mapped('amount'))
        # bluemaxpay = self.env['bluemaxpay.transaction'].search(
        #     [('state', 'in', ['post', 'authorize']), ('sale_id', '=', self.id)])

        amount = sum(manual_paid.mapped('amount'))
        if amount == self.amount_total:
            _logger.error('Already created the Payment')
            raise UserError('Already created the Payment')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Payment',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'sale.order.payment',
            'context': {
                'default_sale_id': self.id,
                'default_currency_id': self.currency_id.id,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_total - amount,
            }
        }
