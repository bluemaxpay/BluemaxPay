import logging
from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Transaction
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# Capture
class SaleOrderCapture(models.Model):
    _name = 'sale.order.capture'
    _description = "Sale Order Capture"

    transaction_id = fields.Many2one('payment.transaction', readonly=True)
    bluemaxpay_transaction_id = fields.Many2one(
        'bluemaxpay.transaction', readonly=True)
    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one('res.currency')

    def capture_amount(self):
        """capture payment"""
        if self.bluemaxpay_transaction_id.transaction:
            bluemaxpay = self.env.ref(
                'payment_bluemaxpay.payment_acquirer_bluemaxpay')

            config = ServicesConfig()
            config.secret_api_key = bluemaxpay.secret_api_key
            config.developer_id = bluemaxpay.developer_id
            config.version_number = bluemaxpay.version_number
            config.service_url = bluemaxpay._get_bluemaxpay_urls()
            ServicesContainer.configure(config)
            ServicesContainer.configure(config)
            address = Address()
            address.address_type = 'Billing'
            if not self.transaction_id.partner_id.city or not self.transaction_id.partner_id.zip or not self.transaction_id.partner_id.state_id or not self.transaction_id.partner_id.country_id or not self.transaction_id.partner_id.street:
                raise UserError(
                    "Customer Address, City, State, Zip and Country fields are not set. These are required for payments.")
            address.postal_code = self.transaction_id.partner_id.zip
            address.country = self.transaction_id.partner_id.country_id.name
            if not self.transaction_id.partner_id.state_id.name == "Armed Forces Americas":
                address.state = self.transaction_id.partner_id.state_id.name
            address.city = self.transaction_id.partner_id.city
            address.street_address_1 = self.transaction_id.partner_id.street
            address.street_address_2 = self.transaction_id.partner_id.street2
            card = CreditCardData()
            card.token = self.bluemaxpay_transaction_id.card_id.token
            try:
                response = Transaction.from_id(self.bluemaxpay_transaction_id.transaction) \
                    .capture(self.amount) \
                    .execute()
                if response.response_code != '00':
                    raise UserError(
                        "{} : Please Check your Credentials and Cards details.".format(response.response_message))
            except ApiException as e:
                _logger.error(e)
                raise UserError(e)
            if response.response_code == '00':
                if self.bluemaxpay_transaction_id.response_log:
                    self.bluemaxpay_transaction_id.response_log += f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
                else:
                    self.bluemaxpay_transaction_id.response_log = f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
                self.bluemaxpay_transaction_id.un_capture_amount = self.bluemaxpay_transaction_id.amount - self.amount
                self.bluemaxpay_transaction_id.captured_amount = self.amount
                self.bluemaxpay_transaction_id.is_capture = True
                self.transaction_id.captured_amount = self.bluemaxpay_transaction_id.captured_amount
                self.bluemaxpay_transaction_id.state = 'post'
                self.bluemaxpay_transaction_id.transaction_id.state = 'done'
                self.bluemaxpay_transaction_id.transaction_id.sudo()._reconcile_after_done()
        else:
            _logger.error(
                _("You can't capture this payment without the Transaction reference"))
            raise UserError(
                _("You can't capture this payment without the Transaction reference"))
