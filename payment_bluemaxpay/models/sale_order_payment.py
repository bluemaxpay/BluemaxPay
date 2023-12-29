import logging
from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Transaction
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# capture
class SaleOrderPayment(models.Model):
    _name = "sale.order.payment"
    _description = "Sale Advance Payment"

    name = fields.Char("Card Holder Name")
    sale_id = fields.Many2one('sale.order')
    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one('res.currency')
    partner_id = fields.Many2one('res.partner', readonly=True)
    card_id = fields.Many2one(
        'bluemax.token', domain="[('partner_id', '=', partner_id)]")
    payment_type = fields.Selection(
        [('authorize', 'Authorize'), ('capture', 'Authorize and Capture')], default="capture")
    is_card = fields.Boolean('Credit Card Manual')
    save_card = fields.Boolean('Save Card')
    token_name = fields.Char('Name On Card')
    card_number = fields.Char('Card Number', size=16)
    card_cvv = fields.Char('Card CVV', size=4)
    card_expiry_month = fields.Char('Expiry Month', size=2)
    card_expiry_year = fields.Char('Expiry Year', size=4)
    card_type = fields.Selection(string="Card Type", selection=[(
        'am_express', 'American Express'), ('other', 'Other'), ], required=False, default='other')
    is_bluemaxpay_card_sale = fields.Boolean()
    s_response_message = fields.Char('Response Message')

    def create_payment(self):
        if not self.is_bluemaxpay_card_sale:
            if not self.is_card:
                if self.card_id:
                    if self.card_id.token:
                        bluemaxpay = self.env.ref(
                            'payment_bluemaxpay.payment_acquirer_bluemaxpay')
                        config = ServicesConfig()
                        config.secret_api_key = bluemaxpay.secret_api_key
                        config.service_url = bluemaxpay._get_bluemaxpay_urls()
                        config.developer_id = bluemaxpay.developer_id
                        config.version_number = bluemaxpay.version_number
                        ServicesContainer.configure(config)
                        card = CreditCardData()
                        card.token = self.card_id.token
                        address = Address()
                        address.address_type = 'Billing'
                        if self.sale_id.partner_shipping_id:
                            if not self.sale_id.partner_shipping_id.city or not self.sale_id.partner_shipping_id.state_id or not self.sale_id.partner_shipping_id.country_id:
                                raise UserError("Delivery Address City, State, and Country fields are not set. These are required for payments.")
                            address.postal_code = self.sale_id.partner_shipping_id.zip
                            if not self.sale_id.partner_shipping_id.state_id.name == "Armed Forces Americas":
                                address.state = self.sale_id.partner_shipping_id.state_id.name
                            address.country = self.sale_id.partner_shipping_id.country_id.name
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
                        if self.payment_type == 'authorize':
                            try:
                                response = card.authorize(self.amount) \
                                    .with_currency(self.currency_id.name) \
                                    .with_address(address) \
                                    .execute()
                            except ApiException as e:
                                _logger.error(e)
                                raise UserError(e)
                        elif self.payment_type == 'capture':
                            try:
                                response = card.authorize(self.amount) \
                                    .with_currency(self.currency_id.name) \
                                    .with_address(address) \
                                    .execute()

                                Transaction.from_id(response.transaction_id) \
                                    .capture(self.amount) \
                                    .execute()
                            except ApiException as e:
                                _logger.error(e)
                                raise UserError(e)
                        elif not self.payment_type:
                            try:
                                response = card.charge(self.amount) \
                                    .with_currency(self.currency_id.name) \
                                    .with_address(address) \
                                    .execute()
                            except ApiException as e:
                                _logger.error(e)
                                raise UserError(e)
                        if self.payment_type == 'capture':
                            transaction = self.env['payment.transaction'].create({
                                'provider_id': bluemaxpay.id,
                                'reference': self.sale_id.name + str(fields.Datetime.now()),
                                'partner_id': self.partner_id.id,
                                'provider_reference': response.reference_number,
                                'sale_order_ids': [(4, self.sale_id.id)],
                                'amount': self.amount,
                                'currency_id': self.env.company.currency_id.id,
                                'state': 'draft',
                                'captured_amount': self.amount
                            })
                            bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                                'name': self.sale_id.name,
                                'amount': self.amount,
                                'card_id': self.card_id.id,
                                'partner_id': self.partner_id.id,
                                'reference': response.reference_number,
                                'date': fields.Datetime.now(),
                                'state': 'draft',
                                'captured_amount': self.amount,
                                'sale_id': self.sale_id.id,
                                'transaction': response.transaction_id,
                                'transaction_id': transaction.id,
                                'payment_type': self.payment_type,
                            })
                        else:
                            transaction = self.env['payment.transaction'].create({
                                'provider_id': bluemaxpay.id,
                                'reference': self.sale_id.name + str(fields.Datetime.now()),
                                'partner_id': self.partner_id.id,
                                'provider_reference': response.reference_number,
                                'sale_order_ids': [(4, self.sale_id.id)],
                                'amount': self.amount,
                                'currency_id': self.env.company.currency_id.id,
                                'state': 'draft',
                                # 'captured_amount': bluemaxpay.captured_amount
                            })
                            bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                                'name': self.sale_id.name,
                                'amount': self.amount,
                                'card_id': self.card_id.id,
                                'partner_id': self.partner_id.id,
                                'reference': response.reference_number,
                                'date': fields.Datetime.now(),
                                'state': 'draft',
                                'sale_id': self.sale_id.id,
                                'transaction': response.transaction_id,
                                'transaction_id': transaction.id,
                                'payment_type': self.payment_type,
                            })
                        transaction.bluemaxpay_trans_id = bluemaxpay_trans.id
                        if response.response_code == '00':
                            if self.payment_type == 'authorize':
                                transaction._set_authorized()
                                bluemaxpay_trans.state = 'authorize'
                                bluemaxpay_trans.un_capture_amount = self.amount
                            else:
                                bluemaxpay_trans.state = 'post'
                                transaction._set_done()
                                transaction._create_payment()
                                transaction._reconcile_after_done()
                        else:
                            transaction._set_canceled()
                            bluemaxpay_trans.state = 'cancel'
                    else:
                        _logger.error(
                            _('Generate token for %s', self.partner_id.name))
                        raise UserError(
                            _('Generate token for %s', self.partner_id.name))
                else:
                    _logger.error(
                        _('Please add BlueMax Pay token for customer  %s  from Invoicing>configuration>bluemaxpayopay token', self.partner_id.name))
                    raise UserError(
                        _('Please add BlueMax Pay token for customer  %s from  from Invoicing>configuration>bluemaxpayopay token', self.partner_id.name))
            else:
                if self.card_number and self.name and self.card_expiry_month and self.card_expiry_year and self.card_cvv:
                    if len(self.card_number) == 16 and self.card_type == 'am_express':
                        _logger.error(
                            _('Card Number must be 15 digits for American Express'))
                        raise UserError(
                            _('Card Number must be 15 digits for American Express'))

                    if len(self.card_number) == 15 and self.card_type == 'other':
                        _logger.error(
                            _('Card Number must be 16 digits for other Cards'))
                        raise UserError(
                            _('Card Number must be 16 digits for other Cards'))

                        if len(self.card_number) != 15 or len(self.card_number) != 16:
                            _logger.error(
                                _('Card Number must be 15 digits for American Express or 16 digits for other Cards'))
                            raise UserError(
                                _('Card Number must be 15 digits for American Express or 16 digits for other Cards'))
                    if len(self.card_expiry_year) != 4:
                        _logger.error(_('Exp year must be 4 digits'))

                        raise UserError(_('Exp year must be 4 digits'))
                    if len(self.card_expiry_month) != 2:
                        _logger.error(_('Exp Month must be 2 digits'))

                        raise UserError(_('Exp Month must be 2 digits'))
                else:
                    _logger.error(_('Add all details'))
                    raise UserError(_('Add all details'))
                bluemaxpay = self.env.ref(
                    'payment_bluemaxpay.payment_acquirer_bluemaxpay')
                config = ServicesConfig()
                config.secret_api_key = bluemaxpay.secret_api_key
                config.service_url = bluemaxpay._get_bluemaxpay_urls()
                config.developer_id = bluemaxpay.developer_id
                config.version_number = bluemaxpay.version_number
                ServicesContainer.configure(config)

                card = CreditCardData()
                card.number = self.card_number
                card.exp_month = self.card_expiry_month
                card.exp_year = self.card_expiry_year
                card.cvn = self.card_cvv
                card.card_holder_name = self.name

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
                        raise UserError("Delivery Address City, State, and Country fields are not set. These are required for payments.")
                    address.postal_code = self.partner_id.zip
                    address.country = self.partner_id.country_id.name
                    if not self.partner_id.state_id.name == "Armed Forces Americas":
                        address.state = self.partner_id.state_id.name
                    address.city = self.partner_id.city
                    address.street_address_1 = self.partner_id.street
                    address.street_address_1 = self.partner_id.street2
                if self.save_card:
                    try:
                        save_card = card.verify() \
                            .with_address(address) \
                            .with_request_multi_use_token(True) \
                            .execute()
                        card_save = self.env['bluemax.token'].create({
                            'name': self.token_name,
                            'partner_id': self.partner_id.id,
                            'active': True
                        })
                        print(save_card.__dict__)
                        if save_card.response_code == '00':
                            card_save.token = save_card.token

                            card.token = save_card.token
                    except ApiException as e:
                        _logger.error(e)
                        raise UserError(e)
                if self.payment_type == 'authorize':
                    try:
                        response = card.authorize(self.amount) \
                            .with_currency(self.currency_id.name) \
                            .with_address(address) \
                            .execute()
                        print('fvd', response)
                    except ApiException as e:
                        _logger.error(e)
                        raise UserError(e)
                elif self.payment_type == 'capture':
                    try:
                        response = card.authorize(self.amount) \
                            .with_currency(self.currency_id.name) \
                            .with_address(address) \
                            .execute()
                        Transaction.from_id(response.transaction_id) \
                            .capture(self.amount) \
                            .execute()
                    except ApiException as e:
                        _logger.error(e)
                        raise UserError(e)
                elif not self.payment_type:
                    try:
                        response = card.charge(self.amount) \
                            .with_currency(self.currency_id.name) \
                            .with_address(address) \
                            .execute()
                    except ApiException as e:
                        _logger.error(e)
                        raise UserError(e)
                if self.payment_type == 'capture':
                    transaction = self.env['payment.transaction'].create({
                        'provider_id': bluemaxpay.id,
                        'reference': self.sale_id.name + ':' + str(fields.Datetime.now()),
                        'partner_id': self.partner_id.id,
                        'provider_reference': response.reference_number,
                        'sale_order_ids': [(4, self.sale_id.id)],
                        'amount': self.amount,
                        'captured_amount': self.amount,
                        'currency_id': self.env.company.currency_id.id,
                        'state': 'draft',
                    })
                    bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                        'name': self.sale_id.name,
                        'amount': self.amount,
                        'card_id': self.card_id.id,
                        'partner_id': self.partner_id.id,
                        'reference': response.reference_number,
                        'date': fields.Datetime.now(),
                        'state': 'draft',
                        'sale_id': self.sale_id.id,
                        'captured_amount': self.amount,
                        'transaction': response.transaction_id,
                        'transaction_id': transaction.id,
                        'payment_type': self.payment_type,
                    })
                else:
                    transaction = self.env['payment.transaction'].create({
                        'provider_id': bluemaxpay.id,
                        'reference': self.sale_id.name + ':' + str(fields.Datetime.now()),
                        'partner_id': self.partner_id.id,
                        'provider_reference': response.reference_number,
                        'sale_order_ids': [(4, self.sale_id.id)],
                        'amount': self.amount,
                        'currency_id': self.env.company.currency_id.id,
                        'state': 'draft',
                    })
                    bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                        'name': self.sale_id.name,
                        'amount': self.amount,
                        'card_id': self.card_id.id,
                        'partner_id': self.partner_id.id,
                        'reference': response.reference_number,
                        'date': fields.Datetime.now(),
                        'state': 'draft',
                        'sale_id': self.sale_id.id,
                        'transaction': response.transaction_id,
                        'transaction_id': transaction.id,
                        'payment_type': self.payment_type,
                    })
                transaction.bluemaxpay_trans_id = bluemaxpay_trans.id
                if response.response_code == '00':
                    if self.payment_type == 'authorize':
                        transaction._set_authorized()
                        bluemaxpay_trans.state = 'authorize'
                        bluemaxpay_trans.un_capture_amount = self.amount
                        self.sale_id.message_post(body=_(
                            "The bluemaxpay transaction with reference: %s for %s has been authorized (BlueMax Pay).",
                            self.sale_id.name, self.amount))
                    else:
                        bluemaxpay_trans.state = 'post'
                        transaction._set_done()
                        transaction._create_payment()
                        transaction._reconcile_after_done()
                        self.sale_id.message_post(body=_(
                            "The bluemaxpay transaction with reference: %s for %s has been Completed (BlueMax Pay).",
                            self.sale_id.name, self.amount))
                else:
                    transaction._set_canceled()
                    bluemaxpay_trans.state = 'cancel'
        else:
            active_order = self.env[self.env.context.get('active_model')].browse(
                self.env.context.get('active_id'))
            if active_order.response_message != '000000':
                active_order.response_message = ' '
                _logger.error("Can't process this payment")
                raise UserError("Can't process this payment")
            active_order.response_message = ''
            bluemaxpay = self.env.ref(
                'payment_bluemaxpay.payment_acquirer_bluemaxpay')
            transaction = self.env['payment.transaction'].create({
                'provider_id': bluemaxpay.id,
                'reference': self.sale_id.name + ':' + str(fields.Datetime.now()),
                'partner_id': self.partner_id.id,
                'provider_reference': '12334',
                'sale_order_ids': [(4, self.sale_id.id)],
                'amount': self.amount,
                'currency_id': self.env.company.currency_id.id,
                'state': 'draft',
            })
            bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                'name': self.sale_id.name,
                'amount': self.amount,
                'card_id': self.card_id.id,
                'partner_id': self.partner_id.id,
                'reference': active_order.transaction_id,
                'date': fields.Datetime.now(),
                'state': 'draft',
                'sale_id': self.sale_id.id,
                'transaction': active_order.transaction_id,
                'transaction_id': transaction.id,
            })
            bluemaxpay_trans.state = 'post'
            transaction._set_done()
            transaction._create_payment()
            transaction._reconcile_after_done()
