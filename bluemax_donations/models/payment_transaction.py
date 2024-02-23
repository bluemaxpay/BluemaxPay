from odoo import fields, models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    donation_payment = fields.Boolean(string="Donation Payment?")
