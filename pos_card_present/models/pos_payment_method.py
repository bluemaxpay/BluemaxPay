from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.pos_card_present.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.pos_card_present.globalpayments.api.entities import Address, Transaction
from odoo.addons.pos_card_present.globalpayments.api.entities.exceptions import ApiException
from odoo.addons.pos_card_present.globalpayments.api.payment_methods import CreditCardData
import logging
_logger = logging.getLogger(__name__)


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'
    _description = 'Payment method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('card_present', 'Card present')]

    port = fields.Char('Port')
    ip_address = fields.Char('IPAddress')
    time_out = fields.Char('Time Out')
    version_num = fields.Char("Version Number.")

    def get_payment_method_details(self):
        return {
            'ip': self.ip_address,
            'port': self.port,
            'timeout': self.time_out,
            'version': self.version_num
        }

    def refund_bluemaxpay_payment_amount(self, transaction_id, amount):
        payload = []
        print(self, amount)
        payment_method = self
        if payment_method:
            config = ServicesConfig()
            config.secret_api_key = 'skapi_cert_MdDoAQA9OV8AtHvi0bQOj9lswEIv5sU4uuOpONdWWQ'
            config.developer_id = '002914'
            config.version_number = 5296
            config.service_url = 'http://cert.api2.heartlandportico.com'
            ServicesContainer.configure(config)
        card = CreditCardData()
        address = Address()
        address.postal_code = '12345'
        try:
            response = card.refund(amount).with_currency(
                self.env.company.currency_id.name).with_transaction_id(transaction_id).execute()
            print(response.__dict__)
            return {
                'response_code': response.response_code,
                'reference_number': response.reference_number,
                'response': response
            }
        except ApiException as e:
            print(e)
            return e
