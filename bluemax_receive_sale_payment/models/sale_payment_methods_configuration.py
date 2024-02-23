
from odoo import api, fields, models


class BlueMaxPayConfiguration(models.Model):
    _name = 'sale.payment.methods'
    _description = 'Sale & Invoice Payment Methods Configuration'
    _rec_name = 'journal_id'

    sequence = fields.Integer('Sequence')
    payment_method_line_id = fields.Many2one('account.payment.method.line', string='Select Payment Method', required=True, readonly=False, store=True, compute='_compute_payment_method_line_id',domain="[('id', 'in', available_payment_method_line_ids),('code','not in',['bluemaxpay','bluemaxpay_card_present'])]")
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Select Journal", store=True, readonly=False, precompute=True, 
        domain=lambda self: [('type', 'in', ('bank', 'cash')), ('company_id', '=', self.env.user.company_id.id)])
    available_payment_method_line_ids = fields.Many2many('account.payment.method.line', compute='_compute_payment_method_line_fields')

    @api.depends('journal_id')
    def _compute_payment_method_line_fields(self):
        for wizard in self:
            if wizard.journal_id:
                wizard.available_payment_method_line_ids = wizard.journal_id._get_available_payment_method_lines('inbound')
            else:
                wizard.available_payment_method_line_ids = False

    @api.depends('journal_id')
    def _compute_payment_method_line_id(self):
        for wizard in self:
            if wizard.journal_id:
                available_payment_method_lines = wizard.journal_id._get_available_payment_method_lines('inbound')
            else:
                available_payment_method_lines = False

            # Select the first available one by default.
            if available_payment_method_lines:
                wizard.payment_method_line_id = available_payment_method_lines[0]._origin
            else:
                wizard.payment_method_line_id = False


