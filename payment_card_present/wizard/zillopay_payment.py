from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.payment_card_present.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_card_present.globalpayments.api.entities import Address
from odoo.addons.payment_card_present.globalpayments.api.entities import EncryptionData, Transaction
from odoo.addons.payment_card_present.globalpayments.api.entities.exceptions import ApiException
from odoo.addons.payment_card_present.globalpayments.api.payment_methods import CreditCardData, CreditTrackData
import logging
_logger = logging.getLogger(__name__)


class ZillopayPayment(models.Model):
    _name = 'zillopay.payment'
    _description = 'Zillopay Payment'

    amount = fields.Monetary('Amount', readonly=True)
    currency_id = fields.Many2one('res.currency')
    payment_id = fields.Many2one('account.payment', readonly=True)
    payment_type = fields.Selection([('authorize', 'Authorize'), ('capture', 'Authorize and Capture')],
                                    default="capture")
    is_card = fields.Boolean('Credit Card Manual')
    save_card = fields.Boolean('Save Card')
    card_name = fields.Char('Card Holder Name')
    token_name = fields.Char('Name On Card')
    payment_method_line_id = fields.Many2one('account.payment.method.line')
    card_number = fields.Char('Card Number', size=16)
    card_cvv = fields.Char('Card CVV', size=4)
    card_expiry_month = fields.Char('Expiry Month', size=2)
    card_expiry_year = fields.Char('Expiry Year', size=4)
    card_type = fields.Selection(string="Card Type",
                                 selection=[('am_express', 'American Express'), ('other', 'Other'), ], required=False,
                                 default='other')
    is_zillo_card_sale = fields.Boolean()
    is_zillo_card_sale_present = fields.Boolean()
    s_response_message = fields.Char('Response Message')

    def action_done(self):
        if self.payment_method_line_id.name == 'zillopay':
            if self.is_card == False:
                if not self.card_id:
                    _logger.error(
                        _('Please add Zillopay token for customer  %s from Invoicing>>configuration>>zillopay token',
                          self.partner_id.name))
                    raise UserError(
                        _('Please add Zillopay token for customer  %s from Invoicing>>configuration>>zillopay token',
                          self.partner_id.name))
                if self.card_id.token:
                    zillopay = self.env.ref(
                        'payment_zillopay.payment_acquirer_zillopay')
                    payment = self.env['account.payment'].browse(
                        self.env.context.get('active_ids'))
                    if len(payment) > 1:
                        if len(payment.mapped('partner_id')) > 1:
                            raise ValueError(
                                "You can't process the group payment of different customer's invoices")
                    config = ServicesConfig()
                    config.secret_api_key = zillopay.secret_api_key
                    if self.payment_method_line_id.payment_acquirer_id and self.payment_method_line_id.payment_acquirer_id.state == 'enabled':
                        config.service_url = 'https://api2.heartlandportico.com'
                    else:
                        config.service_url = 'https://cert.api2.heartlandportico.com'
                    config.developer_id = zillopay.developer_id
                    config.version_number = zillopay.version_number
                    ServicesContainer.configure(config)
                    address = Address()
                    address.address_type = 'Billing'
                    if payment.partner_shipping_id:
                        address.postal_code = payment.partner_shipping_id.zip
                        address.country = payment.partner_shipping_id.country_id.name
                        address.state = payment.partner_shipping_id.state_id.name
                        address.city = payment.partner_shipping_id.city
                        address.street_address_1 = payment.partner_shipping_id.street
                        address.street_address_2 = payment.partner_shipping_id.street2
                    else:
                        address.postal_code = self.partner_id.zip
                        address.country = self.partner_id.country_id.name
                        address.state = self.partner_id.state_id.name
                        address.city = self.partner_id.city
                        address.street_address_1 = self.partner_id.street
                        address.street_address_2 = self.partner_id.street2
                    card = CreditCardData()
                    card.token = self.card_id.token
                    track = CreditTrackData()
                    track.encryption_data = EncryptionData()
                    track.encryption_data.version = '01'
                    try:
                        response = card.charge(self.amount) \
                            .with_currency(self.currency_id.name) \
                            .with_address(address) \
                            .execute()
                        if response.response_code != '00':
                            raise UserError(
                                "{} : Please Check your Credentials and Cards details.".format(response.response_message))

                    except ApiException as e:
                        _logger.error(e)
                        raise UserError(e)
                    zillopay_trans = self.env['zillopay.transaction'].create({
                        'name': self.communication,
                        'move_id': payment.id if len(payment) == 1 else None,
                        'amount': self.amount,
                        'card_id': self.card_id.id,
                        'partner_id': payment.partner_id.id,
                        'reference': response.reference_number,
                        'date': fields.Datetime.now()
                    })
                    if response.response_code == '00':
                        zillopay_trans.state = 'post'
                        zillopay_trans.transaction = response.transaction_id
                        zillopay_trans.reference = response.reference_number
                    else:
                        zillopay_trans.state = 'cancel'
                else:
                    _logger.error(
                        _('Generate token for %s', self.partner_id.name))
                    raise UserError(
                        _('Generate token for %s', self.partner_id.name))
            else:
                if self.card_number and self.card_name and self.card_expiry_month and self.card_expiry_year and self.card_cvv:
                    if len(self.card_number) == 16 and self.card_type == 'am_express':
                        _logger.error(
                            _('Card Number must be 15 digits for American Express'))
                        raise UserError(
                            _('Card Number must be 15 digits for American Express'))
                    if len(self.card_number) == 15 and self.card_type == 'other':
                        _logger.error(
                            _('Card Number must be 16 digits for other Cards'))
                        raise UserError(
                            _('Card Number must be 16 digit for other Cards'))
                        if len(self.card_number) != 15 or len(self.card_number) != 16:
                            _logger.error(
                                _('Card Number must be 15 digits for American Express or 16 digits for other Cards'))
                    if len(self.card_expiry_year) != 4:
                        _logger.error(_('Expiry year must be 4 digits'))
                        raise UserError('Expiry year must be 4 digits')
                    if len(self.card_expiry_month) != 2:
                        _logger.error(_('Expiry Month must be 2 digits'))
                        raise UserError('Expiry Month must be 2 digits')
                else:
                    _logger.error(_('Add all details'))
                    raise UserError('Add all details')
                zillopay = self.env.ref(
                    'payment_zillopay.payment_acquirer_zillopay')
                payment = self.env['account.payment'].browse(
                    self.env.context.get('active_ids'))
                if not payment.partner_id:
                    raise UserError('Please add Partner')
                if len(payment) > 1:
                    if len(payment.mapped('partner_id')) > 1:
                        raise ValueError(
                            "You can't process the group payment of different customer's invoices")
                config = ServicesConfig()
                config.secret_api_key = zillopay.secret_api_key
                if zillopay and zillopay.state == 'enabled':
                    config.service_url = 'https://api2.heartlandportico.com'
                else:
                    config.service_url = 'https://cert.api2.heartlandportico.com'
                config.developer_id = zillopay.developer_id
                config.version_number = zillopay.version_number
                ServicesContainer.configure(config)
                address = Address()
                address.address_type = 'Billing'
                if payment.partner_shipping_id:
                    address.postal_code = payment.partner_shipping_id.zip
                    address.country = payment.partner_shipping_id.country_id.name if payment.partner_shipping_id.country_id else None
                    address.state = payment.partner_shipping_id.state_id.name if payment.partner_shipping_id.state_id else None
                    address.city = payment.partner_shipping_id.city
                    address.street_address_1 = payment.partner_shipping_id.street
                    address.street_address_2 = payment.partner_shipping_id.street2
                else:
                    address.postal_code = payment.partner_id.zip
                    address.country = payment.partner_id.country_id.name if payment.partner_id.country_id else None
                    address.state = payment.partner_id.state_id.name if payment.partner_id.state_id else None
                    address.city = payment.partner_id.city
                    address.street_address_1 = payment.partner_id.street
                    address.street_address_2 = payment.partner_id.street2
                card = CreditCardData()
                card.number = self.card_number
                card.exp_month = self.card_expiry_month
                card.exp_year = self.card_expiry_year
                card.cvn = self.card_cvv
                card.card_holder_name = self.card_name
                if self.save_card:
                    try:
                        save_card = card.verify() \
                            .with_address(address) \
                            .with_request_multi_use_token(True) \
                            .execute()
                        if save_card.response_code != '00':
                            raise UserError(
                                "{} : Please Check your Credentials and Cards details.".format(response.response_message))

                        card_save = self.env['zillo.token'].create({
                            'name': self.token_name,
                            'partner_id': payment.partner_id.id,
                            'active': True
                        })
                        print(save_card.__dict__)
                        if save_card.response_code == '00':
                            card_save.token = save_card.token

                            card.token = save_card.token
                        else:
                            raise UserError(recm)
                    except ApiException as e:
                        _logger.error(e)
                        raise UserError(e)
                try:
                    response = card.charge(self.amount) \
                        .with_currency(self.currency_id.name) \
                        .with_address(address) \
                        .execute()
                    if response.response_code != '00':
                        raise UserError(
                            "{} : Please Check your Credentials and Cards details.".format(response.response_message))
                except ApiException as e:
                    _logger.error(e)
                    raise UserError(e)
                zillopay_trans = self.env['zillopay.transaction'].create({
                    'name': payment.name,
                    'payment_id': payment.id if len(payment) == 1 else None,
                    'amount': self.amount,
                    'card_id': payment.card_id.id if payment.card_id else None,
                    'partner_id': payment.partner_id.id,
                    'reference': response.reference_number,
                    'date': fields.Datetime.now()
                })
                if response.response_code == '00':
                    zillopay_trans.state = 'post'
                    zillopay_trans.transaction = response.transaction_id
                    zillopay_trans.reference = response.reference_number
                    payment.payment_process = True
                    payment.action_post()
                    transaction = self.env['payment.transaction'].search(
                        [('reference', '=', payment.name)])
                    transaction.reference = zillopay_trans.reference
                    if not transaction:
                        transaction = self.env['payment.transaction'].create({
                            'provider_id': self.env.ref('payment_zillopay.payment_acquirer_zillopay').id,
                            'reference': payment.name,
                            'reference': zillopay_trans.reference,
                            'partner_id': payment.partner_id.id,
                            'payment_id': payment.id,
                            'amount': payment.amount,
                            'currency_id': payment.currency_id.id,
                            'state': 'draft',
                            'zillo_trans_id': zillopay_trans.id
                        })
                    transaction._set_done()
                    zillopay_trans.transaction_id = transaction.id
                    payment.payment_transaction_id = transaction.id
                else:
                    zillopay_trans.state = 'cancel'
