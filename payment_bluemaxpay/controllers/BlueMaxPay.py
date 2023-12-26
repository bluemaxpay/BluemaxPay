import pprint
import logging
from globalpayments.api import ServicesConfig, ServicesContainer
from globalpayments.api.entities import Address, Transaction
from globalpayments.api.entities.exceptions import ApiException
from globalpayments.api.payment_methods import CreditCardData

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class BlueMaxPayController(http.Controller):

    @http.route('/payment/bluemaxpay/transaction/return', type='json', auth='public')
    def test_simulate_payment(self, params):
        _logger.info("received bluemaxpay return data:\n%s",
                     pprint.pformat(params.get('reference',)))
        bluemaxpay_trans = request.env['bluemaxpay.transaction'].sudo().browse(
            params.get('bluemaxpay_transaction'))
        transaction = bluemaxpay_trans.transaction_id
        bluemaxpay_trans.transaction_id = transaction.id
        if bluemaxpay_trans.state == 'authorize':
            transaction._set_authorized()
        elif bluemaxpay_trans.state == 'post':
            transaction._set_done()
            transaction._reconcile_after_done()
        elif bluemaxpay_trans.state == 'cancel':
            transaction._set_canceled()
        else:
            transaction._set_pending()
        return transaction

    @http.route('/payment/bluemaxpay/return', type='json', auth="public", methods=['GET', 'POST'], csrf=False, save_session=False)
    def bluemaxpay_return_from_redirect(self, **data):
        """ BlueMax Pay return """
        _logger.info("received bluemaxpay return data:\n%s",
                     pprint.pformat(data))
        tx_sudo = request.env['payment.transaction'].sudo(
        )._get_tx_from_notification_data('bluemaxpay', data)
        tx_sudo._handle_notification_data('bluemaxpay', data)
        return request.redirect('/payment/status')

    @http.route('/get_bluemaxpay/order', type='json', auth='public', csrf=False)
    def bluemaxpay_sale_order(self, **post):
        """getting Current Order"""
        sale_order_id = request.session.get('sale_order_id')
        invoice = False
        # breakpoint()
        if sale_order_id:
            trans_id = request.session.get('__website_sale_last_tx_id')
        else:
            trans_id = request.session.get('__payment_monitored_tx_id__')
            invoice = True
        return {'sale_order_id': sale_order_id, 'trans_id': trans_id, 'is_invoice': invoice}

    @http.route(['/bluemaxpay/api_key'], type='json', auth="public", website=True)
    def bluemaxpay_key(self):
        """Public API Key"""
        api_key = request.env['payment.provider'].search(
            [('code', '=', 'bluemaxpay')])
        return api_key.public_api_key

    @http.route(['/bluemaxpay/transaction'], type='json', auth="public", website=True)
    def transaction_payment_create(self, **code):
        bluemaxpay = request.env['payment.provider'].sudo().\
            browse(code.get('params').get('code'))

        partner = request.env['res.partner'].sudo().\
            browse(code.get('params').get('partner'))
        response = ''
        # breakpoint()
        if code.get('params').get('trans_id'):
            if code.get('params').get('is_invoice'):
                trans_id = request.env['payment.transaction'].sudo().browse(
                    code.get('params').get('trans_id'))
            else:
                trans_id = request.env['payment.transaction'].sudo().browse(
                    code.get('params').get('trans_id'))
        else:
            trans_id = None
        sale = request.env['sale.order'].sudo().browse(
            code.get('params').get('sale'))
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
        if code.get('params').get('is_card'):
            token = request.env['bluemax.token'].browse(
                int(code.get('params').get('card')))
            card = CreditCardData()
            card.token = token.token
        else:
            try:
                card = CreditCardData()
                card.number = code.get('params').get('number')
                card.exp_month = code.get('params').get('exp_month')
                card.exp_year = code.get('params').get('exp_year')
                card.cvn = code.get('params').get('card_code')
                card.card_holder_name = code.get('params').get('name')
            except ApiException as e:
                return {
                    'error_message': True,
                    'message': e
                }
        address = Address()
        address.address_type = 'Billing'
        if trans_id and trans_id.sale_order_ids and trans_id.sale_order_ids.partner_shipping_id:
            address.postal_code = trans_id.sale_order_ids.partner_shipping_id.zip
            address.country = trans_id.sale_order_ids.partner_shipping_id.country_id.name
            if not trans_id.sale_order_ids.partner_shipping_id.state_id.name == "Armed Forces Americas":
                address.state = trans_id.sale_order_ids.partner_shipping_id.state_id.name
            address.city = trans_id.sale_order_ids.partner_shipping_id.city
            address.street_address_1 = trans_id.sale_order_ids.partner_shipping_id.street
            address.street_address_1 = trans_id.sale_order_ids.partner_shipping_id.street2

        elif trans_id.invoice_ids and trans_id.invoice_ids.partner_shipping_id:
            address.postal_code = trans_id.invoice_ids.partner_shipping_id.zip
            address.country = trans_id.invoice_ids.partner_shipping_id.country_id.name
            if not trans_id.invoice_ids.partner_shipping_id.state_id.name == "Armed Forces Americas":
                address.state = trans_id.invoice_ids.partner_shipping_id.state_id.name
            address.city = trans_id.invoice_ids.partner_shipping_id.city
            address.street_address_1 = trans_id.invoice_ids.partner_shipping_id.street
            address.street_address_1 = trans_id.invoice_ids.partner_shipping_id.street2
        else:
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
        if code.get('params').get('card_save'):
            save_card = card.verify() \
                .with_address(address) \
                .with_request_multi_use_token(True) \
                .execute()
            card_save = request.env['bluemax.token'].sudo().create({
                'name': partner.name,
                'partner_id': partner.id,
                'active': True
            })
            if save_card.response_code == '00':
                card_save.token = save_card.token
                card.token = save_card.token
        if payment_type == 'capture':
            try:
                response = card.authorize(float(code.get('params').get('amount'))) \
                    .with_currency(request.env.user.currency_id.name) \
                    .with_address(address) \
                    .execute()
                Transaction.from_id(
                    response.transaction_reference.transaction_id) \
                    .capture(float(code.get('params').get('amount'))) \
                    .execute()
                    
            except ApiException as e:
                return {
                    'error_message': True,
                    'message': e
                }
        elif payment_type == 'authorize':
            try:
                response = card.authorize(code.get('params').get('amount')) \
                    .with_currency(request.env.company.currency_id.name) \
                    .with_address(address) \
                    .execute()
            except ApiException as e:
                return {
                    'error_message': True,
                    'message': e
                }
        bluemaxpay_trans = request.env['bluemaxpay.transaction'].sudo().create({
            'name': sale.name if sale else (trans_id.invoice_ids.name if trans_id.invoice_ids and len(trans_id.invoice_ids) == 1 else payment_id.name),
            'amount': code.get('params').get('amount'),
            'partner_id': partner.id,
            'date': fields.Datetime.now(),
            'sale_id': sale.id if not trans_id.invoice_ids else None,
            'move_id': trans_id.invoice_ids.id if trans_id.invoice_ids and len(trans_id.invoice_ids) == 1 else None,
            'move_ids': [(6, 0, trans_id.invoice_ids.ids)] if trans_id.invoice_ids and len(trans_id.invoice_ids) > 0 else None,
            'transaction_id': trans_id.id,
            'payment_type': payment_type,
            'currency_id' : request.env.company.currency_id.id,
        })
        if response.response_code == '00':
            bluemaxpay_trans.reference = response.reference_number
            bluemaxpay_trans.transaction = response.transaction_id
            if payment_type == 'authorize':
                bluemaxpay_trans.state = 'authorize'
                bluemaxpay_trans.un_capture_amount = trans_id.amount
            elif payment_type == 'capture':
                bluemaxpay_trans.state = 'post'
                bluemaxpay_trans.transaction = response.transaction_id
                bluemaxpay_trans.captured_amount = trans_id.amount
            bluemaxpay_trans.transaction_id.reference = response.reference_number
        else:
            bluemaxpay_trans.state = 'cancel'
        trans_id.captured_amount = bluemaxpay_trans.captured_amount
        return {
            'error_message': False,
            'bluemaxpay_trans': bluemaxpay_trans.id
        }
