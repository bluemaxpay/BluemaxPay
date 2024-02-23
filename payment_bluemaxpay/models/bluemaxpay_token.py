from odoo import models, fields, api, _
from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class BlueMaxPayToken(models.TransientModel):
    _name = 'bluemaxpay.token'
    _description = 'bluemaxpay token'

    name = fields.Char('Card Holder Name')
    token_id = fields.Many2one('bluemax.token')
    number = fields.Char('Card Number', size=16)
    exp_month = fields.Char('Exp Month', size=2)
    exp_year = fields.Char('Exp Year', size=4)
    partner_id = fields.Many2one('res.partner', related='token_id.partner_id')
    card_type = fields.Selection(string="Card Type",
                                 selection=[('am_express', 'American Express'), ('other', 'Other'), ], required=False,
                                 default='other')

    country_id = fields.Many2one(
        comodel_name='res.country', related='token_id.country_id', string='Country', required=True)
    customer_country_id = fields.Many2one(
        comodel_name='res.country',
        related='token_id.customer_country_id',
        string="Customer Country",
        store=True, readonly=False, required=True)
    customer_state_id = fields.Many2one(
        comodel_name='res.country.state',
        related='token_id.customer_state_id',
        string="Customer State",
        # domain="[('country_id', '=', customer_country_id)]",
        store=True, readonly=False, required=True)
    customer_city = fields.Char(
        string="Customer City",
        related='token_id.customer_city',
        store=True, readonly=False, required=True)
    customer_street = fields.Char(
        string="Customer Street",
        related='token_id.customer_street',
        store=True, readonly=False, required=True)
    customer_zip = fields.Char(
        string="Customer Zip",
        related='token_id.customer_zip',
        store=True, readonly=False, required=True)
    _skip_onchange_states = fields.Boolean(default=False)

    @api.onchange('customer_country_id')    
    def onchange_country(self):
        if self.customer_state_id.country_id.id != self.customer_country_id.id:
            self.customer_state_id = False
            self._skip_onchange_states = True

    @api.onchange('customer_state_id')
    def onchange_states(self):
        if not self._skip_onchange_states:
            self.customer_country_id = self.customer_state_id.country_id.id
        self._skip_onchange_states = False


    cvv = fields.Char('CVV')
    active = fields.Boolean()

    def create_token(self):
        if self.number and self.name and self.exp_year and self.exp_month and self.cvv:
            if len(self.number) == 16 and self.card_type == 'am_express':
                _logger.error(
                    _('Card Number must be 15 digits for American Express'))
                raise UserError(
                    _('Card Number must be 15 digits for American Express'))

            if len(self.number) == 15 and self.card_type == 'other':
                _logger.error(
                    _('Card Number must be 16 digits for other Cards'))
                raise UserError(
                    _('Card Number must be 16 digits for other Cards'))

                if len(self.number) != 15 or len(self.number) != 16:
                    _logger.error(
                        _('Card Number must be 15 digits for American Express or 16 digits for other Cards'))
                    raise UserError(
                        _('Card Number must be 15 digits for American Express or 16 digits for other Cards'))
            if len(self.exp_year) != 4:
                _logger.error(_('Exp year must be 4 digits'))

                raise UserError(_('Exp year must be 4 digits'))
            if len(self.exp_month) != 2:
                _logger.error(_('Exp Month must be 2 digits'))

                raise UserError(_('Exp Month must be 2 digits'))
        else:
            _logger.error(_('Add all details'))

            raise UserError('Add all details')
        bluemaxpay = self.env.ref(
            'payment_bluemaxpay.payment_acquirer_bluemaxpay')
        config = ServicesConfig()
        config.secret_api_key = bluemaxpay.secret_api_key
        if bluemaxpay and bluemaxpay.state == 'enabled':
            config.service_url = 'https://api2.heartlandportico.com'
        else:
            config.service_url = 'https://cert.api2.heartlandportico.com'
        config.developer_id = bluemaxpay.developer_id
        config.version_number = bluemaxpay.version_number
        ServicesContainer.configure(config)
        card = CreditCardData()
        card.number = self.number
        card.exp_month = self.exp_month
        card.exp_year = self.exp_year
        card.cvn = self.cvv
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

        # if not self.partner_id.city or not self.partner_id.zip or not self.partner_id.state_id or not self.partner_id.country_id or not self.partner_id.street:
        #     raise UserError(
        #         "Customer Address, City, State, Zip and Country fields are not set. These are required for card verification.")
        # address.postal_code = self.partner_id.zip
        # address.country = self.partner_id.country_id.name
        # if not self.partner_id.state_id.name == "Armed Forces Americas":
        #     address.state = self.partner_id.state_id.name
        # address.city = self.partner_id.city
        # address.street_address_1 = self.partner_id.street
        # address.street_address_2 = self.partner_id.street2
        try:
            response = card.verify() \
                .with_address(address) \
                .with_request_multi_use_token(True) \
                .execute()
        except ApiException as e:
            _logger.error(e)
            raise UserError(e)
        if response.token:
            self.token_id.token = response.token
            self.token_id.active = True
        if response.token is None:
            _logger.error('Token is Not generated')
            raise UserError('Token is Not generated')
