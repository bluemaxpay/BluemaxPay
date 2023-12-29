
from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    def create_invoices(self):
        """create invoice"""
        sale = self.env['sale.order'].browse(self.env.context.get('active_ids'))
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        return res
