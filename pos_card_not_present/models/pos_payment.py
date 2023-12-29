from odoo import fields, models, api


class POSPayment(models.Model):
    _inherit = 'pos.payment'
    _description = 'Description'

    approved_amount = fields.Monetary(
        string='Approved Amount',
        required=False)
    auth_code = fields.Char(
        string='Auth Code',
        required=False)
    avs_resp = fields.Char(
        string='Avs Response',
        required=False)
    href = fields.Char(
        string='Href',
        required=False)
    device_id = fields.Char(
        string='Device Id',
        required=False)

    transaction = fields.Char(
        string='Transaction',
        required=False)

    bluemaxpay_response = fields.Char(
        string='Response',
        required=False)

    ref_number = fields.Char(
        string='Ref. Number',
        required=False)

    card_number = fields.Char('Card Number')

    def _export_for_ui(self, payment):
        value = super()._export_for_ui(payment)
        value['approved_amount'] = payment.approved_amount
        value['bluemaxpay_response'] = payment.bluemaxpay_response
        value['auth_code'] = payment.auth_code
        value['ref_number'] = payment.ref_number
        value['avs_resp'] = payment.avs_resp
        return value
