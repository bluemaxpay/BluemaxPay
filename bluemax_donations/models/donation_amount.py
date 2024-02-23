from odoo import fields, models


class DonationAmount(models.Model):
    _name = 'donation.amount'
    _description = "Donation Amounts available for website"

    name = fields.Char(string="Amount", required=True)
    amount = fields.Integer(string="Amount in rupees", required=True, default=0)
