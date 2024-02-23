import logging

from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address, Transaction
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class BlueMaxPayInvoice(models.Model):
    _name = 'bluemaxpay.transaction'
    _description = "BlueMax Pay Transaction"
    _order = 'date desc'

    name = fields.Char(required=False)
    reference = fields.Char(readonly=True)
    move_id = fields.Many2one('account.move', 'Invoice', readonly=True)
    payment_id = fields.Many2one('account.Payment', 'Payment', readonly=True)
    move_ids = fields.Many2many(
        string="Invoices", comodel_name='account.move', relation='bluemaxpay_account_invoice_transaction_rel',
        column1='transaction_id', column2='invoice_id', readonly=True, copy=False)
    amount = fields.Monetary('Authorized Amount', readonly=True)
    card_id = fields.Many2one(
        'bluemax.token', 'BlueMax Pay Token', domain="[('partner_id', '=', partner_id)]")
    payment_id = fields.Many2one('account.payment', readonly=True)
    transaction_id = fields.Many2one('payment.transaction', readonly=True)
    terminal_name = fields.Many2one('pax.terminal.configuration', string='Terminal Used', readonly=True)

    date = fields.Datetime(readonly=True)
    partner_id = fields.Many2one('res.partner', 'Customer', readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True)
    sale_id = fields.Many2one('sale.order', readonly=True)
    sale_ids = fields.Many2many(
        string="Sales", comodel_name='sale.order', relation='bluemaxpay_sales_transaction_rel',
        column1='transaction_id', column2='sale_id', readonly=True, copy=False,
    )
    transaction = fields.Char('Transaction Reference', readonly=True)
    payment_type = fields.Selection(
        [('authorize', 'Authorize'), ('capture', 'Authorize and Capture')], readonly=True)
    payment_count = fields.Integer('Payment transaction Count', default=1)
    # capture
    un_capture_amount = fields.Monetary('UnCaptured Amount', readonly=True)
    is_capture = fields.Boolean(string="Is Capture", )
    captured_amount = fields.Monetary(
        string='Captured Amount',
        required=False)
    state = fields.Selection([('draft', 'Draft'), ('post', 'Posted'), (
        'authorize', 'Authorize'), ('cancel', 'Cancelled / Refunded')], default='draft')

    is_pax_terminal_transaction = fields.Boolean(
        string="Is it paid from pax terminal / card present transaction", default=False, readonly=True)

    transaction_type = fields.Text(
        string="Payment Method", default="Card Not Present", readonly=True)

    refund_amount = fields.Monetary(
        string='Refund Amount', readonly=True, default=0)
    refund_reference = fields.Char('Refund Reference', readonly=True)
    response_log = fields.Text('Response Logs', readonly=True)

    # capture

    def action_view_payment_trans(self):
        """view payment transaction"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Transaction',
            'view_mode': 'tree,form',
            'res_model': 'payment.transaction',
            'domain': [('id', '=', self.transaction_id.id)],
            'context': "{'create': False}"
        }

    @api.onchange('un_capture_amount')
    def _onchange_un_capture_amount(self):
        if self.state == 'authorze':
            if self.un_capture_amount == 0:
                self.state = 'posted'
                self.transaction_id.state = 'done'

    def reset_draft(self):
        """reset to draft"""
        self.state = "draft"

    def action_capture(self):
        """capture payment"""
        self.capture_payment()

    def capture_payment(self):
        """Capture Payment from """
        if self.un_capture_amount <= 0:
            raise UserError("Payment is already Captured.")
        if not self.transaction:
            _logger.error(
                _("You can't capture this payment without the Transaction reference"))
            raise UserError(
                _("You can't capture this payment without the Transaction reference"))
        if self.transaction:
            bluemaxpay = self.env.ref(
                'payment_bluemaxpay.payment_acquirer_bluemaxpay')

            config = ServicesConfig()
            config.secret_api_key = bluemaxpay.secret_api_key
            config.developer_id = bluemaxpay.developer_id
            config.version_number = bluemaxpay.version_number
            config.service_url = bluemaxpay._get_bluemaxpay_urls()
            ServicesContainer.configure(config)

            address = Address()
            address.address_type = 'Billing'
            if self.sale_id.partner_shipping_id:
                if not self.sale_id.partner_shipping_id.city or not self.sale_id.partner_shipping_id.zip or not self.sale_id.partner_shipping_id.state_id or not self.sale_id.partner_shipping_id.country_id or not self.sale_id.partner_shipping_id.street:
                    raise UserError(
                        "Delivery Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.sale_id.partner_shipping_id.zip
                address.country = self.sale_id.partner_shipping_id.country_id.name
                if not self.sale_id.partner_shipping_id.state_id.name == "Armed Forces Americas":
                    address.state = self.sale_id.partner_shipping_id.state_id.name
                address.city = self.sale_id.partner_shipping_id.city
                address.street_address_1 = self.sale_id.partner_shipping_id.street
                address.street_address_2 = self.sale_id.partner_shipping_id.street2
            else:
                if not self.partner_id.city or not self.partner_id.zip or not self.partner_id.state_id or not self.partner_id.country_id or not self.partner_id.street:
                    raise UserError(
                        "Customer Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.partner_id.zip
                address.country = self.partner_id.country_id.name
                if not self.partner_id.state_id.name == "Armed Forces Americas":
                    address.state = self.partner_id.state_id.name
                address.city = self.partner_id.city
                address.street_address_1 = self.partner_id.street
                address.street_address_2 = self.partner_id.street2

            card = CreditCardData()
            card.token = self.card_id.token

            card = CreditCardData()
            card.token = self.card_id.token

            try:
                trans = Transaction.from_id(self.transaction) \
                    .capture() \
                    .execute()
            except ApiException as e:
                _logger.error(e)
                raise UserError(e)
            if trans.response_code == '00':
                if self.response_log:
                    self.response_log += f"\n{trans.__dict__}\n{trans.transaction_reference.__dict__}\n{trans.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
                else:
                    self.response_log = f"\n{trans.__dict__}\n{trans.transaction_reference.__dict__}\n{trans.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"

                self.state = 'post'
                self.transaction_id.state = 'done'
                self.transaction_id._reconcile_after_done()

    def create_transaction(self):
        """create transaction"""
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
            config.service_url = bluemaxpay._get_bluemaxpay_urls()
            ServicesContainer.configure(config)
            address = Address()
            address.address_type = 'Billing'
            if self.sale_id.partner_shipping_id:
                if not self.sale_id.partner_shipping_id.city or not self.sale_id.partner_shipping_id.zip or not self.sale_id.partner_shipping_id.state_id or not self.sale_id.partner_shipping_id.country_id or not self.sale_id.partner_shipping_id.street:
                    raise UserError(
                        "Delivery Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.sale_id.partner_shipping_id.zip
                address.country = self.sale_id.partner_shipping_id.country_id.name
                if not self.sale_id.partner_shipping_id.state_id.name == "Armed Forces Americas":
                    address.state = self.sale_id.partner_shipping_id.state_id.name
                address.city = self.sale_id.partner_shipping_id.city
                address.street_address_1 = self.sale_id.partner_shipping_id.street
                address.street_address_2 = self.sale_id.partner_shipping_id.street2
            else:
                if not self.partner_id.city or not self.partner_id.zip or not self.partner_id.state_id or not self.partner_id.country_id or not self.partner_id.street:
                    raise UserError(
                        "Customer Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.partner_id.zip
                address.country = self.partner_id.country_id.name
                if not self.partner_id.state_id.name == "Armed Forces Americas":
                    address.state = self.partner_id.state_id.name
                address.city = self.partner_id.city
                address.street_address_1 = self.partner_id.street
                address.street_address_2 = self.partner_id.street2
            card = CreditCardData()
            card.token = self.card_id.token

            try:
                response = card.charge(round(self.amount, 2)) \
                    .with_currency('USD') \
                    .with_address(address) \
                    .execute()
                if response.response_code != '00':
                    raise UserError(
                        "{} : Please Check your Credentials and Cards details.".format(response.response_message))
            except ApiException as e:
                _logger.error(e)
                raise UserError(e)
            if response.response_code == '00':
                if self.response_log:
                    self.response_log += f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
                else:
                    self.response_log = f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"

                if self.transaction_id:
                    self.transaction_id.state = 'draft'
                    self.transaction_id._set_done()
                    self.transaction_id.payment_id.state = 'posted'
                else:
                    transaction = self.env['payment.transaction'].create({
                        'reference': self.move_id.name,
                        'partner_id': self.partner_id.id,
                        'amount': self.amount,
                        'provider_id': bluemaxpay.id,
                        'currency_id': self.move_id.currency_id.id,
                        'invoice_ids': [(4, self.move_id.id, None)],
                        'state': 'done',
                        # 'captured_amount': bluemaxpay.captured_amount
                    })
                    self.transaction_id = transaction.id
                    transaction._create_payment()
                self.state = 'post'
                self.transaction = response.transaction_id
            pass
        else:
            _logger.error(_('Generate token for %s', self.partner_id.name))
            raise UserError(_('Generate token for %s', self.partner_id.name))

    def void_transaction(self):
        """Cancel transation"""
        if not self.transaction:
            _logger.error(
                _("You can't capture this payment without the Transaction reference"))
            raise UserError(
                _("You can't capture this payment without the Transaction reference"))
        if self.transaction:
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
            if self.sale_id.partner_shipping_id:
                if not self.sale_id.partner_shipping_id.city or not self.sale_id.partner_shipping_id.zip or not self.sale_id.partner_shipping_id.state_id or not self.sale_id.partner_shipping_id.country_id or not self.sale_id.partner_shipping_id.street:
                    raise UserError(
                        "Delivery Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.sale_id.partner_shipping_id.zip
                address.country = self.sale_id.partner_shipping_id.country_id.name
                if not self.sale_id.partner_shipping_id.state_id.name == "Armed Forces Americas":
                    address.state = self.sale_id.partner_shipping_id.state_id.name
                address.city = self.sale_id.partner_shipping_id.city
                address.street_address_1 = self.sale_id.partner_shipping_id.street
                address.street_address_2 = self.sale_id.partner_shipping_id.street2
            else:
                if not self.partner_id.city or not self.partner_id.zip or not self.partner_id.state_id or not self.partner_id.country_id or not self.partner_id.street:
                    raise UserError(
                        "Customer Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.partner_id.zip
                address.country = self.partner_id.country_id.name
                if not self.partner_id.state_id.name == "Armed Forces Americas":
                    address.state = self.partner_id.state_id.name
                address.city = self.partner_id.city
                address.street_address_1 = self.partner_id.street
                address.street_address_2 = self.partner_id.street2
            card = CreditCardData()
            card.token = self.card_id.token
            try:
                void_transaction = Transaction.from_id(self.transaction) \
                    .void() \
                    .execute()
            except ApiException as e:
                _logger.error(e)
                raise UserError(e)
            if void_transaction.response_code == '00':
                if self.response_log:
                    self.response_log += f"\n{void_transaction.__dict__}\n{void_transaction.transaction_reference.__dict__}\n{void_transaction.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
                else:
                    self.response_log = f"\n{void_transaction.__dict__}\n{void_transaction.transaction_reference.__dict__}\n{void_transaction.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"

                self.move_id.payment_state = 'not_paid'
                self.transaction_id.state = 'draft'
                self.transaction_id._set_pending()
                self.transaction_id._set_canceled()
                self.state = 'cancel'

    def refund_transaction(self):
        """Cancel transation"""
        if not self.transaction:
            _logger.error(
                _("You can't capture this payment without the Transaction reference"))
            raise UserError(
                _("You can't capture this payment without the Transaction reference"))
        if self.transaction:
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
            if self.sale_id.partner_shipping_id:
                if not self.sale_id.partner_shipping_id.city or not self.sale_id.partner_shipping_id.zip or not self.sale_id.partner_shipping_id.state_id or not self.sale_id.partner_shipping_id.country_id or not self.sale_id.partner_shipping_id.street:
                    raise UserError(
                        "Delivery Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.sale_id.partner_shipping_id.zip
                address.country = self.sale_id.partner_shipping_id.country_id.name
                if not self.sale_id.partner_shipping_id.state_id.name == "Armed Forces Americas":
                    address.state = self.sale_id.partner_shipping_id.state_id.name
                address.city = self.sale_id.partner_shipping_id.city
                address.street_address_1 = self.sale_id.partner_shipping_id.street
                address.street_address_2 = self.sale_id.partner_shipping_id.street2
            else:
                if not self.partner_id.city or not self.partner_id.zip or not self.partner_id.state_id or not self.partner_id.country_id or not self.partner_id.street:
                    raise UserError(
                        "Customer Address, City, State, Zip and Country fields are not set. These are required for payments.")
                address.postal_code = self.partner_id.zip
                address.country = self.partner_id.country_id.name
                if not self.partner_id.state_id.name == "Armed Forces Americas":
                    address.state = self.partner_id.state_id.name
                address.city = self.partner_id.city
                address.street_address_1 = self.partner_id.street
                address.street_address_2 = self.partner_id.street2
            card = CreditCardData()
            card.token = self.card_id.token
            try:
                refund_transaction = Transaction.from_id(self.transaction) \
                    .refund(self.captured_amount) \
                    .with_currency("USD") \
                    .execute()
            except ApiException as e:
                _logger.error(e)
                raise UserError(e)
            if refund_transaction.response_code == '00':
                if self.response_log:
                    self.response_log += f"\n{refund_transaction.__dict__}\n{refund_transaction.transaction_reference.__dict__}\n{refund_transaction.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
                else:
                    self.response_log = f"\n{refund_transaction.__dict__}\n{refund_transaction.transaction_reference.__dict__}\n{refund_transaction.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"

                self.move_id.payment_state = 'not_paid'
                self.transaction_id.state = 'draft'
                self.refund_amount = self.captured_amount
                self.refund_reference = refund_transaction.transaction_reference.transaction_id
                self.transaction_id._set_pending()
                self.transaction_id._set_canceled()
                self.state = 'cancel'
