from odoo import fields, models


class DonationAmount(models.Model):
    _name = 'donation.amount'
    _description = "Donation Amounts available for website"
    _order = "sequence, id"

    def _default_sequence(self):
        cat = self.search([], limit=1, order="sequence DESC")
        if cat:
            return cat.sequence + 5
        return 10000

    # name = fields.Char(string="Amount", required=True)
    sequence = fields.Integer(string='Sequence', index=True, default=_default_sequence)
    amount = fields.Integer(string="Amount", required=True, default=0)
