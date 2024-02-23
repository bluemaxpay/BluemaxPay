import logging
from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address, Transaction
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException
from stdnum.exceptions import ValidationError
from odoo.exceptions import UserError

from odoo import _, api, fields, models
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    amount = fields.Monetary(
        string="Authorized Amount", currency_field='currency_id', readonly=True, required=True)
    bluemaxpay_trans_id = fields.Many2one(
        'bluemaxpay.transaction', 'BlueMax Pay transaction')
    bluemaxpay_trans_count = fields.Integer(
        'BlueMax Pay Transaction Count', default=1)
    captured_amount = fields.Monetary(
        string='Captured Amount',
        required=False)
    payment_type = fields.Selection(
        string='type',
        required=False, related="bluemaxpay_trans_id.payment_type")
    payment_method_id = fields.Many2one(
        string="Payment Method", comodel_name='payment.method', readonly=True, required=False
    )

    def action_view_bluemaxpay_trans(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'BlueMax Pay Transaction',
            'view_mode': 'tree,form',
            'res_model': 'bluemaxpay.transaction',
            'domain': [('id', '=', self.bluemaxpay_trans_id.id)],
            'context': "{'create': False}"
        }

    def transaction_payment_create(self, card_details, code):
        bluemaxpay = self.env['payment.provider'].sudo(). \
            browse(code.get('code'))
        partner = self.env['res.partner'].sudo(). \
            browse(code.get('partner'))
        response = ''
        sale = self.env['sale.order'].sudo().browse(code.get('sale'))
        try:
            config = ServicesConfig()
            config.secret_api_key = bluemaxpay.secret_api_key
            config.developer_id = bluemaxpay.developer_id
            config.version_number = bluemaxpay.version_number
            config.service_url = bluemaxpay._get_bluemaxpay_urls()
            ServicesContainer.configure(config)
        except ApiException as e:
            return {
                'error_message': True,
                'message': e
            }
        if card_details.get('is_card'):
            token = self.env['bluemax.token'].browse(
                int(card_details.get('card')))
            card = CreditCardData()
            card.token = token.token
        else:
            try:
                card = CreditCardData()
                card.number = card_details.get('number')
                card.exp_month = card_details.get('exp_month')
                card.exp_year = card_details.get('exp_year')
                card.cvn = card_details.get('card_code')
                card.card_holder_name = card_details.get('name')
            except ApiException as e:
                return {
                    'error_message': True,
                    'message': e
                }
        address = Address()
        address.address_type = 'Billing'
        if self.sale_order_ids and self.sale_order_ids.partner_shipping_id:
            if not self.sale_order_ids.partner_shipping_id.city or not self.sale_order_ids.partner_shipping_id.zip or not self.sale_order_ids.partner_shipping_id.state_id or not self.sale_order_ids.partner_shipping_id.country_id or not self.sale_order_ids.partner_shipping_id.street:
                raise UserError(
                    "Sale Delivery Address, City, State, Zip and Country fields are not set. These are required for payments.")
            address.postal_code = self.sale_order_ids.partner_shipping_id.zip
            address.country = self.sale_order_ids.partner_shipping_id.country_id.name
            if not self.sale_order_ids.partner_shipping_id.state_id.name == "Armed Forces Americas":
                address.state = self.sale_order_ids.partner_shipping_id.state_id.name
            address.city = self.sale_order_ids.partner_shipping_id.city
            address.street_address_1 = self.sale_order_ids.partner_shipping_id.street
            address.street_address_2 = self.sale_order_ids.partner_shipping_id.street2
        elif self.invoice_ids and self.invoice_ids.partner_shipping_id:
            if not self.invoice_ids.partner_shipping_id.city or not self.invoice_ids.partner_shipping_id.zip or not self.invoice_ids.partner_shipping_id.state_id or not self.invoice_ids.partner_shipping_id.country_id or not self.invoice_ids.partner_shipping_id.street:
                raise UserError(
                    "Invoice Delivery Address, City, State, Zip and Country fields are not set. These are required for payments.")
            address.postal_code = self.invoice_ids.partner_shipping_id.zip
            address.country = self.invoice_ids.partner_shipping_id.country_id.name
            if not self.invoice_ids.partner_shipping_id.state_id.name == "Armed Forces Americas":
                address.state = self.invoice_ids.partner_shipping_id.state_id.name
            address.city = self.invoice_ids.partner_shipping_id.city
            address.street_address_1 = self.invoice_ids.partner_shipping_id.street
            address.street_address_2 = self.invoice_ids.partner_shipping_id.street2
        else:
            if not partner.city or not partner.zip or not partner.state_id or not partner.country_id or not partner.street:
                raise UserError(
                    "Customer Delivery Address, City, State, Zip and Country fields are not set. These are required for payments.")
            address.postal_code = partner.zip if partner else None
            address.country = partner.country_id.name if partner else None
            if not partner.state_id.name == "Armed Forces Americas":
                address.state = partner.state_id.name if partner else None
            address.city = partner.city if partner else None
            address.street_address_1 = partner.street if partner else None
            address.street_address_2 = partner.street2 if partner else None
        payment_type = bluemaxpay.payment_type
        if not payment_type:
            return {
                'error_message': True,
                'message': 'Invalid BlueMax Pay payment type'
            }
        if card_details.get('card_save'):
            save_card = card.verify() \
                .with_address(address) \
                .with_request_multi_use_token(True) \
                .execute()
            if save_card.response_code != '00':
                raise UserError(
                    "{} : Please Check your Credentials and Cards details.".format(response.response_message))
            card_save = self.env['bluemax.token'].sudo().create({
                'name': self.env.user.partner_id.name,
                'partner_id': self.env.user.partner_id.id,
                'active': True
            })
            if save_card.response_code == '00':
                card_save.token = save_card.token
                card.token = save_card.token
        if payment_type == 'capture':
            try:
                response = card.authorize(float(code.get('amount'))) \
                    .with_currency(self.env.user.currency_id.name) \
                    .with_address(address) \
                    .execute()
                if response.response_code != '00':
                    raise UserError(
                        "{} : Please Check your Credentials and Cards details.".format(response.response_message))
                Transaction.from_id(
                    response.transaction_reference.transaction_id) \
                    .capture(float(code.get('amount'))) \
                    .execute()
            except ApiException as e:
                return {
                    'error_message': True,
                    'message': e
                }
        elif payment_type == 'authorize':
            try:
                response = card.authorize(code.get('amount')) \
                    .with_currency(self.env.company.currency_id.name) \
                    .with_address(address) \
                    .execute()
                if response.response_code != '00':
                    raise UserError(
                        "{} : Please Check your Credentials and Cards details.".format(response.response_message))
            except ApiException as e:
                return {
                    'error_message': True,
                    'message': e
                }
        bluemaxpay_trans = self.env['bluemaxpay.transaction'].create({
            'name': sale.name,
            'amount': code.get('amount'),
            'partner_id': self.env.user.partner_id.id,
            'date': fields.Datetime.now(),
            'sale_id': sale.id,
            'payment_type': payment_type,
        })
        if response.response_code == '00':
            bluemaxpay_trans.reference = response.reference_number
            bluemaxpay_trans.transaction = response.transaction_id
            if payment_type == 'authorize':
                bluemaxpay_trans.state = 'authorize'
                bluemaxpay_trans.un_capture_amount = self.amount

            elif payment_type == 'capture':
                bluemaxpay_trans.state = 'post'
                bluemaxpay_trans.transaction = response.transaction_id
        else:
            bluemaxpay_trans.state = 'cancel'
        return {
            'error_message': False,
            'bluemaxpay_trans': bluemaxpay_trans.id
        }

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """ Override of payment to find the transaction based on Flutterwave data.

        :param str provider_code: The code of the provider that handled the transaction.
        :param dict notification_data: The notification data sent by the provider.
        :return: The transaction if found.
        :rtype: recordset of `payment.transaction`
        :raise ValidationError: If inconsistent data were received.
        :raise ValidationError: If the data match no transaction.
        """

        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'bluemaxpay' or len(tx) == 1:
            return tx

        reference = notification_data
        if not reference:
            raise ValidationError(
                "BlueMax Pay: " + _("Received data with missing reference."))
        tx = self.search([('reference', '=', reference),
                          ('provider_code', '=', provider_code)])
        if not tx:
            raise ValidationError(
                "BlueMax Pay: " +
                _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _bluemaxpay_tokenize_from_feedback_data(self, data):
        """ Create a new token based on the feedback data.

        Note: self.ensure_one()

        :param dict data: The feedback data sent by the provider
        :return: None
        """
        self.ensure_one()

        token = self.env['payment.token'].create({
            'acquirer_id': self.acquirer_id.id,
            'name': payment_utils.build_token_name(data['additionalData'].get('cardSummary')),
            'partner_id': self.partner_id.id,
            'acquirer_ref': data['additionalData']['recurring.recurringDetailReference'],
            'verified': True,  # The payment is authorized, so the payment method is valid
        })
        self.write({
            'token_id': token,
            'tokenize': False,
        })
        _logger.info(
            "created token with id %s for partner with id %s", token.id, self.partner_id.id
        )

    @api.model
    def _get_tx_from_feedback_data(self, code, data):
        """ Override of payment to find the transaction based on transfer data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The transfer feedback data
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(code, data)
        if code != 'bluemaxpay':
            return tx
        # reference = data.get('reference')
        tx = self.search(
            [('reference', '=', data), ('code', '=', 'bluemaxpay')])
        return tx

    def _process_feedback_data(self, data):
        """ Override of payment to process the transaction based on transfer data.

        Note: self.ensure_one()

        :param dict data: The transfer feedback data
        :return: None
        """
        super()._process_feedback_data(data)
        if self.code != 'bluemaxpay':
            return

    def _send_capture_request(self):
        """ Request the code of the acquirer handling the transaction to capture it.

        For an acquirer to support authorization, it must override this method and request a capture
        to its code.

        Note: self.ensure_one()

        :return: None
        """
        bluemaxpay = self.env['bluemaxpay.transaction'].search(
            [('state', '=', 'authorize'), ('transaction_id', '=', self.id)])
        if bluemaxpay:
            bluemaxpay.action_capture()
        self.ensure_one()

    def _send_void_request(self):
        bluemaxpay = self.env['bluemaxpay.transaction'].search([('state', '=', 'authorize'),
                                                                ('transaction_id', '=', self.id)])
        if bluemaxpay:
            bluemaxpay.void_transaction()
        self.ensure_one()
