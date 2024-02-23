from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = "account.payment"

    sale_id = fields.Many2one('sale.order', 'Sale Order', readonly=True)

    sale_count = fields.Integer(
        string='SaleOrder', compute='_get_saleorder_count', readonly=True)
    sale_payment_method = fields.Many2one('sale.payment.methods', string="Sale Payment Method", readonly=True)
    def _get_saleorder_count(self):
        for record in self:
            record.sale_count = self.env['sale.order'].search_count(
                [('id', '=', record.sale_id.id)])

    def action_view_saleorder(self):
        action = self.env.ref(
            'sale.action_quotations_with_onboarding').read([])[0]
        saleorder = self.env['sale.order'].search(
            [('id', '=', self.sale_id.id)])
        action['domain'] = [('id', 'in', saleorder.ids)]
        return action
