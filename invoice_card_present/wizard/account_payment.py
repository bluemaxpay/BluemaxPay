from odoo import models, fields


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    is_card_present = fields.Boolean('Card Present')
    response_message = fields.Char('Response Message')
