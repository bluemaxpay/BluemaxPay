from odoo.addons.payment import utils as payment_utils
import requests
import logging
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Sale Order"

    response_message = fields.Char('Response Message')
    response = fields.Text('Pax Terminal Response')
    response_amt = fields.Float('Pax Terminal Amount')
    transaction_id = fields.Char('Transaction id')
    terminal_id = fields.Integer('Terminal ID')
    paymentlink_address_note = fields.Char(
        string='Address', readonly=True)
    paymentlink_card_name = fields.Char(
        string='Name on Card', readonly=True)
    paymentlink_customer_ip = fields.Char(
        string='Transaction IP', readonly=True)
    is_payment_link_paid = fields.Boolean(
        'Is Payment Link Paid', default=False)

    # Geo-location fields
    city = fields.Char(string='City', readonly=True)
    region = fields.Char(string='Region', readonly=True)
    country = fields.Char(string='Country', readonly=True)
    postal = fields.Char(string='Postal Code', readonly=True)
    timezone = fields.Char(string='Timezone', readonly=True)
    loc = fields.Char(string='Geolocation', readonly=True)
    org = fields.Char(string='ISP', readonly=True)
    map_image = fields.Binary(string='Map Image', readonly=True)

    @api.model
    def get_geolocation(self, ip_address):
        try:
            ipurl = f'https://ipinfo.io/{ip_address}'
            response = requests.get(ipurl)
            data = response.json()
            static_map_url = f'https://chabloz.eu/map/staticmap.php?'
            params = {
                'center': data.get('loc', ''),
                'zoom': 10,
                'size': '400x400',
                'markers': data.get('loc', '')
            }
            response = requests.get(static_map_url, params=params)
            image_data = response.content
            self.city = data.get('city', '')
            self.region = data.get('region', '')
            self.country = data.get('country', '')
            self.postal = data.get('postal', '')
            self.timezone = data.get('timezone', '')
            self.loc = data.get('loc', '')
            self.org = data.get('org', '')
            self.map_image = base64.b64encode(image_data)
        except Exception as e:
            pass

    def _get_access_token(self):
        self.ensure_one()
        return payment_utils.generate_access_token(
            self.partner_id.id, self.amount_total - sum(self.invoice_ids.filtered(
                lambda x: x.state != 'cancel' and x.invoice_line_ids.sale_line_ids.order_id == self).mapped('amount_total')), self.currency_id.id
        )

    def _get_payment_link_amount(self):
        self.ensure_one()
        return self.amount_total - sum(self.invoice_ids.filtered(lambda x: x.state != 'cancel' and x.invoice_line_ids.sale_line_ids.order_id == self).mapped('amount_total'))

    def get_response_message(self, get_response_message, ResponseId, response, terminal_id, ResponseApproveAmt):
        self.response_message = get_response_message
        self.transaction_id = ResponseId
        self.response = response
        self.terminal_id = terminal_id
        self.response_amt = ResponseApproveAmt

        return self

    def create_payment(self):
        bluemaxpay = self.env['bluemaxpay.transaction'].search(
            [('state', 'in', ['post', 'authorize']), ('sale_id', '=', self.id)])

        amount = sum(bluemaxpay.mapped('amount'))
        if amount == self.amount_total:
            _logger.error('Already created the Payment')
            raise UserError('Already created the Payment')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Payment',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'sale.order.payment',
            'context': {
                'default_sale_id': self.id,
                'default_currency_id': self.currency_id.id,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_total - amount,
            }
        }


# capture


    def payment_action_capture(self):

        if self.partner_shipping_id:
            if not self.partner_shipping_id.city or not self.partner_shipping_id.zip or not self.partner_shipping_id.state_id or not self.partner_shipping_id.country_id or not self.partner_shipping_id.street:
                raise UserError(
                    "Delivery Address, City, State, Zip and Country fields are not set. These are required for payments.")

        else:
            if not self.partner_id.city or not self.partner_id.zip or not self.partner_id.state_id or not self.partner_id.country_id or not self.partner_id.street:
                raise UserError(
                    "Customer Address, City, State, Zip and Country fields are not set. These are required for payments.")

        bluemaxpay = self.env['bluemaxpay.transaction'].search(
            [('state', 'in', ['post', 'authorize']), ('sale_id', '=', self.id)], limit=1)
        if bluemaxpay.is_capture:
            raise UserError(_('Payment is already captured.'))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Payment',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'sale.order.capture',
            'context': {
                'default_bluemaxpay_transaction_id': bluemaxpay.id,
                'default_transaction_id': bluemaxpay.transaction_id.id,
                'default_currency_id': bluemaxpay.currency_id.id,
                'default_amount': bluemaxpay.un_capture_amount,
            }
        }
