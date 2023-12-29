# coding: utf-8

from odoo import _, fields, models, api


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    def _get_payment_terminal_selection(self):
        return super()._get_payment_terminal_selection() + [('bluemax', 'Bluemax')]


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    pos_payment_terminal = fields.Selection(
        related='payment_method_id.use_payment_terminal', string="Payment Terminal", store=True)

    def action_open_bluemax_txns(self):
        bluemax_txns = self.env['bluemax.pos.payment'].search([
            ('payment_method_id', '=', self.payment_method_id.id),
            ('order_id', '=', self.pos_order_id.pos_reference.replace('Order ', '')),
        ]).ids
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bluemax Transactions'),
            'res_model': 'bluemax.pos.payment',
            'view_type': 'list',
            'view_mode': 'list',
            'views': [[False, 'list']],
            'domain': [('id', 'in', bluemax_txns)],
        }
