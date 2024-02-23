from odoo import fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.addons.pos_card_present.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.pos_card_present.globalpayments.api.entities import Address
from odoo.addons.pos_card_present.globalpayments.api.entities.exceptions import ApiException
from odoo.addons.pos_card_present.globalpayments.api.entities import Transaction
from odoo.addons.pos_card_present.globalpayments.api.payment_methods import CreditCardData
import logging
_logger = logging.getLogger(__name__)


class PosPayment(models.Model):
    """Interit to add fields for stripe payment terminals """
    _inherit = "pos.payment"

    bluemaxpay_transaction = fields.Char(
        string="BlueMax Transaction ID:", required=False, )
    refunded_id = fields.Char(string="BlueMax Refund ID", required=False, )

    state = fields.Selection([
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], default='done', string='Status', readonly=True)



    def pos_void(self):
        if not self.transaction_id:
            raise UserError('BlueMax Pay Transaction does not exist')
        config = ServicesConfig()
        config.secret_api_key = self.payment_method_id.secret_api_key
        config.developer_id = self.payment_method_id.developer_id
        config.version_number = self.payment_method_id.version_number
        if self.payment_method_id.state == 'enabled':
            config.service_url = 'https://api2.heartlandportico.com'
        else:
            config.service_url = 'https://cert.api2.heartlandportico.com'
        ServicesContainer.configure(config)
        address = Address()
        address.postal_code = '12345'
        try:
            if self.transaction_id:
                void_transaction = Transaction.from_id(self.transaction_id) \
                    .refund(self.amount) \
                    .with_currency("USD") \
                    .execute()
                self.write({'state': 'cancel'})
            else:
                raise UserError('BlueMax Pay Transaction does not exist')
        except ApiException as e:
            _logger.error(e)
            raise UserError(e)
