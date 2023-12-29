import logging
from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import EncryptionData
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData, CreditTrackData

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    acquirer_id = fields.Many2one(
        'payment.provider', 'Acquirrer', domain="[('code', '=', 'bluemaxpay')]")
    acquirer = fields.Selection([('bluemaxpay', 'BlueMax Pay')])
    is_bluemaxpay = fields.Boolean(string='BlueMax Pay')
    card_id = fields.Many2one(
        'bluemax.token', 'BlueMax Pay Token', domain="[('partner_id', '=', partner_id)]")
    save_card = fields.Boolean('Save Card')
    is_card = fields.Boolean('Credit Card Manual')
    card_name = fields.Char('Card Holder Name')
    token_name = fields.Char('Name On Card')
    card_number = fields.Char('Card Number', size=16)
    card_cvv = fields.Char('Card CVV', size=4)
    card_expiry_month = fields.Char('Expiry Month', size=2)
    card_expiry_year = fields.Char('Expiry Year', size=4)
    card_type = fields.Selection(string="Card Type",
                                 selection=[('am_express', 'American Express'), ('other', 'Other'), ], required=False,
                                 default='other')

    @api.onchange('payment_method_line_id')
    def _onchange_is_bluemaxpay(self):
        """change is_bluemaxpay"""
        if self.payment_method_line_id.code == 'bluemaxpay':
            self.is_bluemaxpay = True
        else:
            self.is_bluemaxpay = False

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        first_batch_result = batches[0]
        edit_mode = self.can_edit_wizard and (
            len(batches[0]['lines']) == 1 or self.group_payment)
        to_process = []
        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard(
                first_batch_result)
            to_process.append({
                'create_vals': payment_vals,
                'to_reconcile': batches[0]['lines'],
                'batch': batches[0],
            })
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })
        payments = self._init_payments(to_process, edit_mode=edit_mode)
        self._post_payments(to_process, edit_mode=edit_mode)
        if self.is_bluemaxpay:
            bluemaxpay = self.env['bluemaxpay.transaction'].search([('name', '=', self.communication), ('state', '=', 'post')],
                                                                   limit=1)
            if bluemaxpay.state == 'post':
                payments.state = 'posted'
                transaction = self.env['payment.transaction'].search(
                    [('reference', '=', self.communication)])
                transaction.provider_reference = bluemaxpay.reference
                if not transaction:
                    transaction = self.env['payment.transaction'].create({
                        'provider_id': self.env.ref('payment_bluemaxpay.payment_acquirer_bluemaxpay').id,
                        'reference': self.communication,
                        'provider_reference': bluemaxpay.reference,
                        'partner_id': self.partner_id.id,
                        'payment_id': payments.id,
                        'amount': self.amount,
                        'currency_id': self.currency_id.id,
                        'state': 'draft',
                        'bluemaxpay_trans_id': bluemaxpay.id,
                        'captured_amount': bluemaxpay.captured_amount
                    })
                transaction._set_done()
                bluemaxpay.transaction_id = transaction.id

        self._reconcile_payments(to_process, edit_mode=edit_mode)
        return payments

    def action_create_payments(self):
        if self.payment_method_line_id.code == 'bluemaxpay':
            if self.is_card == False:
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
                    move = self.env['account.move'].search(
                        [('id', '=', self.env.context.get('active_id'))])
                    if len(move) > 1:
                        if len(move.mapped('partner_id')) > 1:
                            raise ValueError(
                                "You can't process the group payment of different customer's invoices")

                    config = ServicesConfig()
                    config.secret_api_key = bluemaxpay.secret_api_key
                    config.service_url = self.payment_method_line_id.payment_provider_id._get_bluemaxpay_urls()
                    config.developer_id = bluemaxpay.developer_id
                    config.version_number = bluemaxpay.version_number

                    ServicesContainer.configure(config)
                    address = Address()
                    address.address_type = 'Billing'
                    if move.partner_shipping_id:
                        if not move.partner_shipping_id.city or not move.partner_shipping_id.state_id or not move.partner_shipping_id.country_id:
                            raise UserError(
                                "Delivery Address City, State, and Country fields are not set. These are required for payments.")
                        address.postal_code = move.partner_shipping_id.zip
                        address.country = move.partner_shipping_id.country_id.name
                        if not move.partner_shipping_id.state_id.name == "Armed Forces Americas":
                            address.state = move.partner_shipping_id.state_id.name
                        address.city = move.partner_shipping_id.city
                        address.street_address_1 = move.partner_shipping_id.street
                        address.street_address_1 = move.partner_shipping_id.street2
                    else:
                        if not self.partner_id.city or not self.partner_id.state_id or not self.partner_id.country_id:
                            raise UserError(
                                "Customer Address City, State, and Country fields are not set. These are required for payments.")
                        address.postal_code = self.partner_id.zip
                        address.country = self.partner_id.country_id.name
                        if not self.partner_id.state_id.name == "Armed Forces Americas":
                            address.state = self.partner_id.state_id.name
                        address.city = self.partner_id.city
                        address.street_address_1 = self.partner_id.street
                        address.street_address_1 = self.partner_id.street2

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
                    except ApiException as e:
                        _logger.error(e)
                        raise UserError(e)
                    bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                        'name': self.communication,
                        'move_id': move.id if len(move) == 1 else None,
                        'move_ids': [(6, 0, move.ids)] if len(move) > 0 else None,
                        'amount': self.amount,
                        'card_id': self.card_id.id,
                        'partner_id': move.partner_id.id,
                        'reference': response.reference_number,
                        'date': fields.Datetime.now(),
                        'captured_amount': self.amount
                    })
                    if response.response_code == '00':
                        bluemaxpay_trans.state = 'post'
                        bluemaxpay_trans.transaction = response.transaction_id
                        bluemaxpay_trans.reference = response.reference_number
                    else:
                        bluemaxpay_trans.state = 'cancel'
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
                bluemaxpay = self.env.ref(
                    'payment_bluemaxpay.payment_acquirer_bluemaxpay')
                move = self.env['account.move'].search(
                    [('id', '=', self.env.context.get('active_id'))])
                if len(move) > 1:
                    if len(move.mapped('partner_id')) > 1:
                        raise ValueError(
                            "You can't process the group payment of different customer's invoices")
                config = ServicesConfig()
                config.secret_api_key = bluemaxpay.secret_api_key
                config.service_url = bluemaxpay._get_bluemaxpay_urls()
                config.developer_id = bluemaxpay.developer_id
                config.version_number = bluemaxpay.version_number
                ServicesContainer.configure(config)
                address = Address()
                address.address_type = 'Billing'
                if move.partner_shipping_id:
                    if not move.partner_shipping_id.city or not move.partner_shipping_id.state_id or not move.partner_shipping_id.country_id:
                        raise UserError(
                            "Delivery Address City, State, and Country fields are not set. These are required for payments.")
                    address.postal_code = move.partner_shipping_id.zip
                    address.country = move.partner_shipping_id.country_id.name if move.partner_shipping_id.country_id else None
                    if not move.partner_shipping_id.state_id.name == "Armed Forces Americas":
                        address.state = move.partner_shipping_id.state_id.name if move.partner_shipping_id.state_id else None
                    address.city = move.partner_shipping_id.city
                    address.street_address_1 = move.partner_shipping_id.street
                    address.street_address_1 = move.partner_shipping_id.street2
                else:
                    if not move.partner_id.city or not move.partner_id.state_id or not move.partner_id.country_id:
                        raise UserError(
                            "Customer Address City, State, and Country fields are not set. These are required for payments.")
                    address.postal_code = move.partner_id.zip
                    address.country = move.partner_id.country_id.name if move.partner_id.country_id else None
                    if not move.partner_id.state_id.name == "Armed Forces Americas":
                        address.state = move.partner_id.state_id.name if move.partner_id.state_id else None
                    address.city = move.partner_id.city
                    address.street_address_1 = move.partner_id.street
                    address.street_address_1 = move.partner_id.street2
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
                        card_save = self.env['bluemax.token'].create({
                            'name': self.token_name,
                            'partner_id': move.partner_id.id,
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
                bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
                    'name': self.communication,
                    'move_id': move.id if len(move) == 1 else None,
                    'move_ids': [(6, 0, move.ids)] if len(move) > 0 else None,
                    'amount': self.amount,
                    'card_id': self.card_id.id,
                    'partner_id': move.partner_id.id,
                    'reference': response.reference_number,
                    'date': fields.Datetime.now(),
                    'captured_amount': self.amount
                })
                if response.response_code == '00':
                    bluemaxpay_trans.state = 'post'
                    bluemaxpay_trans.transaction = response.transaction_id
                    bluemaxpay_trans.reference = response.reference_number
                else:
                    bluemaxpay_trans.state = 'cancel'
        res = super(AccountPaymentRegister, self).action_create_payments()
        return res
