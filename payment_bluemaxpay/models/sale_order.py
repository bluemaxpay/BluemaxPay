import logging

from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sale Order"

    response_message = fields.Char('Response Message')
    transaction_id = fields.Char('Transaction id')

    def get_response_message(self, get_response_message, ResponseId):
        self.response_message = get_response_message
        self.transaction_id = ResponseId
        return self

    def create_payment(self):
        bluemaxpay = self.env['bluemaxpay.transaction'].search(
            [('state', 'in', ['post', 'authorize']), ('sale_id', '=', self.id)])

        amount = sum(bluemaxpay.mapped('amount'))
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
# capture

    def payment_action_capture(self):
        bluemaxpay = self.env['bluemaxpay.transaction'].search(
            [('state', 'in', ['post', 'authorize']), ('sale_id', '=', self.id)], limit=1)
        if bluemaxpay.is_capture:
            raise UserError(_('Payment is already captured.'))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Payment',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'sale.order.capture',
            'context': {
                'default_bluemaxpay_transaction_id': bluemaxpay.id,
                'default_transaction_id': bluemaxpay.transaction_id.id,
                'default_currency_id': bluemaxpay.currency_id.id,
                'default_amount': bluemaxpay.un_capture_amount,
            }
        }
