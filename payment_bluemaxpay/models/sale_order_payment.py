import logging
from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Transaction
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException

from odoo import _, fields, models, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderPayment(models.Model):
    _name = "sale.order.payment"
    _description = "Sale Advance Payment"

    save_address = fields.Boolean("Saved Address")
    save_address_name = fields.Char("Name On Address")
    partner_id_child_ids = fields.Many2one(
        'res.partner', string='Select Saved Address', domain="[('parent_id', '=', partner_id), ('type', '!=', 'contact')]")
    pax_config_ids = fields.Many2many(
        'pax.terminal.configuration', string='All Available Pax terminals', readonly=True, compute='_compute_pax_config_ids')

    @api.depends('is_bluemaxpay_card_sale')
    def _compute_pax_config_ids(self):
        pax_config_model = self.env['pax.terminal.configuration']
        pax_configs = pax_config_model.search([])
        self.pax_config_ids = [(6, 0, pax_configs.ids)]
        for pax_config in self.pax_config_ids:
            pax_config.amount_pax = self.amount

    @api.onchange('partner_id_child_ids')
    def onchange_partner_id(self):
        if self.sale_id.partner_shipping_id:
            domain = [('parent_id', '=', self.sale_id.partner_shipping_id.id),
                      ('type', '!=', 'contact')]
        else:
            domain = [('parent_id', '=', self.sale_id.partner_id.id),
                      ('type', '!=', 'contact')]
        return {'domain': {'partner_id_child_ids': domain}}

    country_id = fields.Many2one(
        comodel_name='res.country', string='Country')
    customer_country_id = fields.Many2one(
        comodel_name='res.country',
        string="Customer Country",
        store=True, readonly=False)
    customer_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string="Customer State",
        domain="[('country_id', '=', customer_country_id)]",
        store=True, readonly=False)
    customer_city = fields.Char(
        string="Customer City",
        store=True, readonly=False)
    customer_street = fields.Char(
        string="Customer Street",
        store=True, readonly=False)
    customer_zip = fields.Char(
        string="Customer Zip",
        store=True, readonly=False)

    @api.onchange('partner_id_child_ids')
    def onchange_partner_id_child_ids(self):
        if self.partner_id_child_ids:
            self.customer_country_id = self.partner_id_child_ids.country_id.id
            self.customer_state_id = self.partner_id_child_ids.state_id.id
            self.customer_city = self.partner_id_child_ids.city
            self.customer_street = self.partner_id_child_ids.street
            self.customer_zip = self.partner_id_child_ids.zip
        else:
            if self.sale_id.partner_shipping_id:
                self.customer_country_id = self.sale_id.partner_shipping_id.country_id.id,
                self.customer_state_id = self.sale_id.partner_shipping_id.state_id.id
                self.customer_city = self.sale_id.partner_shipping_id.city
                self.customer_street = self.sale_id.partner_shipping_id.street
                self.customer_zip = self.sale_id.partner_shipping_id.zip
            else:
                self.customer_country_id = self.sale_id.partner_id.country_id.id,
                self.customer_state_id = self.sale_id.partner_id.state_id.id
                self.customer_city = self.sale_id.partner_id.city
                self.customer_street = self.sale_id.partner_id.street
                self.customer_zip = self.sale_id.partner_id.zip

    name = fields.Char("Card Holder Name")
    sale_id = fields.Many2one('sale.order')
    amount = fields.Monetary('Amount')
    currency_id = fields.Many2one('res.currency')
    partner_id = fields.Many2one('res.partner', readonly=True)
    card_id = fields.Many2one(
        'bluemax.token', string="Saved Card", domain="[('partner_id', '=', partner_id)]")
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
    is_bluemaxpay_card_sale = fields.Boolean(string="Credit Card Terminal")
    s_response_message = fields.Char('Response Message')

    def create_payment(self):
        if self.amount < 0:
            raise UserError("Amount can not be negative. For refunds you can use the refund button on the Bluemax Pay Transaction.")
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
                        if not self.card_id.customer_city or not self.card_id.customer_zip or not self.card_id.customer_state_id or not self.card_id.customer_country_id or not self.card_id.customer_street:
                            raise UserError(
                                "Address, City, State, Zip and Country fields are not set for this saved card. These are required for payments.")
                        address.postal_code = self.card_id.customer_zip
                        address.country = self.card_id.customer_country_id.name
                        if not self.card_id.customer_state_id.name == "Armed Forces Americas":
                            address.state = self.card_id.customer_state_id.name
                        address.city = self.card_id.customer_city
                        address.street_address_1 = self.card_id.customer_street

                        if self.payment_type == 'authorize':
                            try:
                                response = card.authorize(self.amount) \
                                    .with_currency(self.currency_id.name) \
                                    .with_address(address) \
                                    .execute()
                                if response.response_code != '00':
                                    raise UserError(
                                        "{} : Please Check your Credentials and Cards details.".format(response.response_message))
                            except ApiException as e:
                                _logger.error(e)
                                raise UserError(e)
                        elif self.payment_type == 'capture':
                            try:
                                response = card.authorize(self.amount) \
                                    .with_currency(self.currency_id.name) \
                                    .with_address(address) \
                                    .execute()
                                if response.response_code != '00':
                                    raise UserError(
                                        "{} : Please Check your Credentials and Cards details.".format(response.response_message))
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
                                if response.response_code != '00':
                                    raise UserError(
                                        "{} : Please Check your Credentials and Cards details.".format(response.response_message))
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
                            if bluemaxpay_trans.response_log:
                                bluemaxpay_trans.response_log += f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
                            else:
                                bluemaxpay_trans.response_log = f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"

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
                if not self.customer_city or not self.customer_zip or not self.customer_state_id or not self.customer_country_id or not self.customer_street:
                    raise UserError(
                        "Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.customer_zip
                address.country = self.customer_country_id.name
                if not self.customer_state_id.name == "Armed Forces Americas":
                    address.state = self.customer_state_id.name
                address.city = self.customer_city
                address.street_address_1 = self.customer_street

                if self.save_card:
                    try:
                        save_card = card.verify() \
                            .with_address(address) \
                            .with_request_multi_use_token(True) \
                            .execute()
                        if save_card.response_code != '00':
                            raise UserError(
                                "{} : Please Check your Credentials and Cards details.".format(response.response_message))
                        card_save = self.env['bluemax.token'].create({
                            'name': self.token_name,
                            'partner_id': self.partner_id.id,
                            'active': True
                        })
                        print(save_card.__dict__)
                        if save_card.response_code == '00':
                            card_save.token = save_card.token
                            card_save.customer_street = self.customer_street
                            card_save.customer_state_id = self.customer_state_id.id
                            card_save.customer_city = self.customer_city
                            card_save.customer_zip = self.customer_zip
                            card_save.customer_country_id = self.customer_country_id.id
                            card.token = save_card.token
                    except ApiException as e:
                        _logger.error(e)
                        raise UserError(e)

                if self.save_address:
                    child_data = {
                        'type': 'other',
                        'name': self.save_address_name,
                        'street': self.customer_street,
                        'state_id': self.customer_state_id.id,
                        'city': self.customer_city,
                        'zip': self.customer_zip,
                        'country_id': self.customer_country_id.id,
                    }

                    if self.sale_id.partner_shipping_id:
                        self.sale_id.partner_shipping_id.write({
                            'child_ids': [(0, 0, child_data)]
                        })
                    else:
                        self.partner_id.write({
                            'child_ids': [(0, 0, child_data)]
                        })

                if self.payment_type == 'authorize':
                    try:
                        response = card.authorize(self.amount) \
                            .with_currency(self.currency_id.name) \
                            .with_address(address) \
                            .execute()
                        if response.response_code != '00':
                            raise UserError(
                                "{} : Please Check your Credentials and Cards details.".format(response.response_message))
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
                        if response.response_code != '00':
                            raise UserError(
                                "{} : Please Check your Credentials and Cards details.".format(response.response_message))

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
                        if response.response_code != '00':
                            raise UserError(
                                "{} : Please Check your Credentials and Cards details.".format(response.response_message))

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
                    if bluemaxpay_trans.response_log:
                        bluemaxpay_trans.response_log += f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
                    else:
                        bluemaxpay_trans.response_log = f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"

                    if self.payment_type == 'authorize':
                        transaction._set_authorized()
                        bluemaxpay_trans.state = 'authorize'
                        bluemaxpay_trans.un_capture_amount = self.amount
                        self.sale_id.message_post(body=_(
                            "The bluemaxpay transaction with reference: %s for %.2f has been authorized (BlueMax Pay)." % (self.sale_id.name, self.amount)))
                    else:
                        bluemaxpay_trans.state = 'post'
                        transaction._set_done()
                        transaction._create_payment()
                        transaction._reconcile_after_done()
                        self.sale_id.message_post(body=_(
                            "The bluemaxpay transaction with reference: %s for %.2f has been Completed (BlueMax Pay)." % (self.sale_id.name, self.amount)))
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
                'amount': active_order.response_amt,
                'currency_id': self.env.company.currency_id.id,
                'state': 'draft',
            })
            bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                'name': self.sale_id.name,
                'amount': active_order.response_amt,
                'card_id': self.card_id.id,
                'partner_id': self.partner_id.id,
                'reference': active_order.transaction_id,
                'date': fields.Datetime.now(),
                'payment_type': 'capture',
                'state': 'draft',
                'sale_id': self.sale_id.id,
                'transaction': active_order.transaction_id,
                'transaction_id': transaction.id,
            })
            if bluemaxpay_trans.response_log:
                bluemaxpay_trans.response_log += f"\n{active_order.response}\n--------------------------------------\n"
            else:
                bluemaxpay_trans.response_log = f"\n{active_order.response}\n--------------------------------------\n"
            bluemaxpay_trans.state = 'post'
            bluemaxpay_trans.terminal_name = self.env['pax.terminal.configuration'].browse(active_order.terminal_id).id
            bluemaxpay_trans.is_pax_terminal_transaction = True
            bluemaxpay_trans.transaction_type = "Card Present / Pax"
            transaction._set_done()
            transaction._create_payment()
            transaction._reconcile_after_done()
