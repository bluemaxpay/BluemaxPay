from odoo import fields, models, _
from odoo.addons.pos_card_present.globalpayments.api.entities import Transaction


class PosOrder(models.Model):
    _inherit = "pos.order"

    bluemaxpay_transaction = fields.Char(
        string="BlueMax Transaction ID:", required=False, )

    def _payment_fields(self, order, ui_paymentline):
        rec = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        rec['refunded_id'] = ui_paymentline.get('refunded_id', False)
        rec['bluemaxpay_transaction'] = ui_paymentline.get(
            'bluemaxpay_transaction', False)
        return rec
