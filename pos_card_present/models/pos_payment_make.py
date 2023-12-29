from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.pos_card_present.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.pos_card_present.globalpayments.api.entities import Address
from odoo.addons.pos_card_present.globalpayments.api.entities.exceptions import ApiException
from odoo.addons.pos_card_present.globalpayments.api.entities import Transaction
from odoo.addons.pos_card_present.globalpayments.api.payment_methods import CreditCardData
import logging
_logger = logging.getLogger(__name__)


class PosMakePaymentInh(models.TransientModel):
    _inherit = 'pos.make.payment'

    def check(self):

        order = self.env['pos.order'].browse(
            self.env.context.get('active_id', False))
        refunded_order = self.env['pos.order'].search(
            [('name', '=', order.name.split(' ')[0])])
        if self.payment_method_id.journal_id.type != 'cash' and self.payment_method_id.use_payment_terminal and \
                self.payment_method_id.use_payment_terminal == 'card_present' or self.payment_method_id.use_payment_terminal == 'card_not_present':
            if refunded_order:
                for payment in refunded_order.payment_ids:
                    if payment.transaction_id and not payment.refunded_id:
                        """Cancel transation"""
                        if not self.card_id:
                            _logger.error(
                                _('Please add BlueMax Pay token for customer  %s from Invoicing>>configuration>>bluemaxpay token',
                                  self.partner_id.name))
                            raise UserError(
                                _('Please add BlueMax Pay token for customer  %s from Invoicing>>configuration>>bluemaxpay token',
                                  self.partner_id.name))
                        if self.card_id.token:
                            bluemaxpay = self.env.ref(
                                'payment_bluemaxpay.payment_acquirer_bluemaxpay')
                            config = ServicesConfig()
                            config.secret_api_key = bluemaxpay.secret_api_key
                            config.developer_id = bluemaxpay.developer_id
                            config.version_number = bluemaxpay.version_number
                            config.service_url = 'http://cert.api2.heartlandportico.com'
                            ServicesContainer.configure(config)
                            ServicesContainer.configure(config)
                            address = Address()
                            address.address_type = 'Billing'
                            if self.sale_id.partner_shipping_id:
                                if not self.sale_id.partner_shipping_id.city or not self.sale_id.partner_shipping_id.state_id or not self.sale_id.partner_shipping_id.country_id:
                                    raise UserError("Delivery Address City, State, and Country fields are not set. These are required for payments.")
                                address.postal_code = self.sale_id.partner_shipping_id.zip
                                address.country = self.sale_id.partner_shipping_id.country_id.name
                                if not self.sale_id.partner_shipping_id.state_id.name == "Armed Forces Americas":
                                    address.state = self.sale_id.partner_shipping_id.state_id.name
                                address.city = self.sale_id.partner_shipping_id.city
                                address.street_address_1 = self.sale_id.partner_shipping_id.street
                                address.street_address_1 = self.sale_id.partner_shipping_id.street2
                            else:
                                if not self.partner_id.city or not self.partner_id.state_id or not self.partner_id.country_id:
                                    raise UserError("Customer Address City, State, and Country fields are not set. These are required for payments.")
                                address.postal_code = self.partner_id.zip
                                address.country = self.partner_id.country_id.name
                                if not self.partner_id.state_id.name == "Armed Forces Americas":
                                    address.state = self.partner_id.state_id.name
                                address.city = self.partner_id.city
                                address.street_address_1 = self.partner_id.street
                                address.street_address_1 = self.partner_id.street2
                            card = CreditCardData()
                            card.token = self.card_id.token
                        try:
                            void_transaction = Transaction.from_id(payment.transaction_id) \
                                .void() \
                                .execute()
                            trans = void_transaction
                            print(trans)
                        except ApiException as e:
                            _logger.error(e)
                            raise UserError(e)
                    else:
                        raise ValidationError('The Payment against this order is not done through stripe '
                                              'terminal so you can not refund it through this payment method.'
                                              ' Please select other payment method.')
            else:
                raise ValidationError(
                    'Odoo Error... Please try to refund with other payment method')
        else:
            res = super(PosMakePaymentInh, self).check()
            return res
