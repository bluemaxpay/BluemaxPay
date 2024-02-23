import logging

from odoo import fields, models, api, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    card_present = fields.Boolean()
    payment_process = fields.Boolean()
    card_not_present = fields.Boolean()
    response_message = fields.Char('Response Message')
    transaction_id = fields.Char('Transaction id')
    save_token = fields.Many2one('bluemax.token', string='Saved Card')

    @api.onchange('payment_method_line_id')
    def _onchange_payment_method_line(self):
        """payment method"""
        if self.payment_method_line_id.code == 'bluemaxpay_card_present':
            self.card_present = True
        elif self.payment_method_line_id.code == 'bluemaxpay':
            self.card_present = True
        else:
            self.card_present = False
            self.card_not_present = False

    def get_response_message(self, ResponseCode, ResponseId):
        _logger.error("Could not parse file %s: %s" %
                      (ResponseCode, ResponseId))
        self.response_message = ResponseCode
        self.transaction_id = ResponseId

        return self

    def action_post(self):
        for payment in self:
            if payment.card_present and not payment.payment_process:
                if not payment.partner_id:
                    raise UserError("Add a customer")
                transaction = self.env['payment.transaction'].create({
                    'provider_id': self.env.ref('payment_bluemaxpay.payment_acquirer_bluemaxpay').id,
                    'reference': payment.name + ': ' + str(fields.Datetime.now()),
                    'partner_id': payment.partner_id.id or None,
                    'amount': payment.amount,
                    'currency_id': payment.currency_id.id,
                    'payment_id': payment.id,
                })
                bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                    'name': payment.name,
                    'amount': payment.amount,
                    'partner_id': payment.partner_id.id or None,
                    'date': fields.Datetime.now(),
                    'transaction_id': transaction.id,
                    'payment_type': 'capture',
                    'move_id': payment.move_id.id,
                })
                if payment.response_message != '000000':
                    payment.response_message = ''
                    raise UserError("Can't process this payment")
                else:
                    bluemaxpay_trans.reference = payment.transaction_id
                    bluemaxpay_trans.transaction = payment.transaction_id
                    transaction.provider_reference = payment.transaction_id
                    bluemaxpay_trans.state = 'post'
                    transaction.bluemaxpay_trans_id = bluemaxpay_trans.id
                    transaction._set_done()
        return super(AccountPayment, self).action_post()

    def action_payment(self):
        if self.amount <= 0:
            raise UserError('Payment Amount should be Greater than 0')
        if not self.partner_id:
            raise UserError("You can't proceed the payment without customer.")
        card_present = False
        card_not_present = False
        if self.payment_method_line_id.code == 'bluemaxpay_card_present':
            card_present = True
        if self.payment_method_line_id.code == 'bluemaxpay':
            card_not_present = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Payment',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'bluemaxpay.payment',
            'context': {
                'default_payment_id': self.id,
                'default_amount': self.amount,
                'card_id' : self.save_token,
                'default_is_bluemaxpay_card_sale': card_not_present,
                'default_is_bluemaxpay_card_sale_present': card_present,
                'default_currency_id': self.currency_id.id,
                'default_payment_method_line_id': self.payment_method_line_id.id,
                'default_is_card': False,
            }
        }
