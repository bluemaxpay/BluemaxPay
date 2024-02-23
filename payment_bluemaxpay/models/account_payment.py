from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException
import logging
_logger = logging.getLogger(__name__)


class AccountPaymentMethodLineInherit(models.Model):
    _inherit = "account.payment.method.line"

    payment_method_id = fields.Many2one(
        string='Payment Method',
        comodel_name='account.payment.method',
        domain="[('payment_type', '=?', payment_type), ('id', 'in', available_payment_method_ids)]",
        ondelete="cascade",
        required=True
    )

class AccountPayment(models.Model):
    _inherit = "account.payment"
    _description = "payment"

    card_id = fields.Many2one(
        'bluemax.token', domain="[('partner_id', '=', partner_id)]")
    is_card = fields.Boolean()
    save_token = fields.Many2one('bluemax.token', string='Saved Card')

    # @api.onchange('payment_method_line_id')
    # def _onchange_payment_method_line_id(self):
    #     """payment method"""
    #     if self.payment_method_line_id.code == 'bluemaxpay':
    #         self.is_card = True
    #     else:
    #         self.is_card = False

    # def action_post(self):
    #     """post payment"""
    #     for rec in self:
    #         if rec.payment_method_line_id.code == 'bluemaxpay' and rec.is_card:
    #             if not rec.partner_id:
    #                 _logger.error(_('Add Customer details'))
    #                 raise UserError('Add Customer details')
    #             if not rec.card_id:
    #                 _logger.error(_('Add Card details'))
    #                 raise UserError('Add Card details')
    #             else:
    #                 if not rec.card_id.token:
    #                     _logger.error(
    #                         _('Generate token for %s', rec.partner_id.name))
    #                     raise UserError(
    #                         _('Generate token for %s', rec.partner_id.name))
    #                 else:
    #                     if rec.amount > 0.00:
    #                         bluemaxpay = rec.env.ref(
    #                             'payment_bluemaxpay.payment_acquirer_bluemaxpay')
    #                         config = ServicesConfig()
    #                         config.secret_api_key = bluemaxpay.secret_api_key
    #                         if bluemaxpay and bluemaxpay.state == 'enabled':
    #                             config.service_url = 'https://api2.heartlandportico.com'
    #                         else:
    #                             config.service_url = 'https://cert.api2.heartlandportico.com'
    #                         config.developer_id = bluemaxpay.developer_id
    #                         config.version_number = bluemaxpay.version_number
    #                         ServicesContainer.configure(config)
    #                         card = CreditCardData()
    #                         card.token = rec.card_id.token
    #                         address = Address()
    #                         address.address_type = 'Billing'
    #                         if not rec.partner_id.city or not rec.partner_id.zip or not rec.partner_id.state_id or not rec.partner_id.country_id or not rec.partner_id.street:
    #                             raise UserError(
    #                                 "Customer Address, City, State, Zip and Country fields are not set. These are required for payments.")
    #                         address.postal_code = rec.partner_id.zip
    #                         address.country = rec.partner_id.country_id.name
    #                         if not rec.partner_id.state_id.name == "Armed Forces Americas":
    #                             address.state = rec.partner_id.state_id.name
    #                         address.city = rec.partner_id.city
    #                         address.street_address_1 = rec.partner_id.street
    #                         address.street_address_1 = rec.partner_id.street2
    #                         try:
    #                             response = card.charge(rec.amount).with_currency(rec.currency_id.name) \
    #                                 .with_address(address).execute()
    #                             if response.response_code != '00':
    #                                 raise UserError(
    #                                     "{} : Please Check your Credentials and Cards details.".format(response.response_message))
    #                         except ApiException as e:
    #                             _logger.error(e)
    #                             raise UserError(e)
    #                         transaction = rec.env['payment.transaction'].create({
    #                             'provider_id': bluemaxpay.id,
    #                             'reference': rec.name + ': ' + str(
    #                                 fields.Datetime.now()),
    #                             'partner_id': rec.partner_id.id,
    #                             'amount': rec.amount,
    #                             'currency_id': rec.currency_id.id,
    #                             'payment_id': rec.id,
    #                         })
    #                         bluemaxpay_trans = rec.env['bluemaxpay.transaction'].create({
    #                             'name': rec.name,
    #                             'amount': rec.amount,
    #                             'partner_id': rec.partner_id.id,
    #                             'date': fields.Datetime.now(),
    #                             'move_id': rec.id,
    #                             'card_id': rec.card_id.id,
    #                             'transaction_id': transaction.id,
    #                             'payment_type': 'capture',
    #                         })
    #                         rec.payment_transaction_id = transaction.id
    #                         if response.response_code == '00':
    #                             bluemaxpay_trans.reference = response.reference_number
    #                             bluemaxpay_trans.transaction = response.transaction_id
    #                             transaction.provider_reference = response.reference_number
    #                             bluemaxpay_trans.state = 'post'
    #                             transaction.bluemaxpay_trans_id = bluemaxpay_trans.id
    #                             transaction._set_done()
    #                         else:
    #                             rec.state = 'draft'
    #                     else:
    #                         _logger.error(
    #                             _("Can't process a payment with 0.00 amount"))
    #                         raise UserError(
    #                             "Can't process a payment with 0.00 amount")
    #     res = super(AccountPayment, self).action_post()
    #     return res

    def action_draft(self):
        """action draft"""
        if self.payment_method_line_id.code == 'bluemaxpay':
            for rec in self:
                if rec.payment_transaction_id.state in ['done', 'authorized']:
                    _logger.error(
                        "Can't draft a payment with transaction state in confirmed or authorized")
                    raise UserError(
                        "Can't draft a payment with transaction state in confirmed or authorized")
        res = super(AccountPayment, self).action_draft()
        return res
