from odoo import fields, models, api


class PosOrder(models.Model):
    """Inherit to Populate the refunded_Id value from JS"""
    _inherit = "pos.order"

    def _payment_fields(self, order, ui_paymentline):
        rec = super(PosOrder, self)._payment_fields(order, ui_paymentline)
        rec['approved_amount'] = ui_paymentline.get('approved_amount', False)
        rec['bluemaxpay_response'] = ui_paymentline.get(
            'bluemaxpay_response', False)
        rec['ref_number'] = ui_paymentline.get('ref_number', False)
        rec['auth_code'] = ui_paymentline.get('auth_code', False)
        rec['avs_resp'] = ui_paymentline.get('avs_resp', False)
        rec['transaction'] = ui_paymentline.get('transaction', False)
        rec['href'] = ui_paymentline.get('href', False)
        rec['device_id'] = ui_paymentline.get('device_id', False)
        return rec
