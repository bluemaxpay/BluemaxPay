import pprint
import logging
from odoo.addons.payment_bluemaxpay.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities import Address, Transaction
from odoo.addons.payment_bluemaxpay.globalpayments.api.entities.exceptions import ApiException
from odoo.addons.payment_bluemaxpay.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.portal.controllers import portal
from odoo import fields, http, _
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
        if sale_order_id:
            trans_id = request.session.get('__website_sale_last_tx_id')
            # invoice = True
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
        if code.get('params').get('trans_id'):
            if code.get('params').get('is_invoice'):
                trans_id = request.env['payment.transaction'].sudo().browse(
                    code.get('params').get('trans_id'))
            else:
                trans_id = request.env['payment.transaction'].sudo().browse(
                    code.get('params').get('trans_id'))
        else:
            trans_id = None
        sale = request.env['sale.order'].sudo().browse(code.get('params').get('sale'))
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
            token = request.env['bluemax.token'].browse(int(code.get('params').get('card')))
            card = CreditCardData()
            card.token = token.token
        else:
            try:
                if code.get('params').get('card_code') == '' or code.get('params').get('number') == '' or code.get('params').get('exp_month') == '' or code.get('params').get('exp_year') == '' or code.get('params').get('name') == '':
                    if trans_id.sale_order_ids:
                        trans_id.sale_order_ids.message_post(body=_(
                            "Website: The bluemaxpay transaction was unsuccessful : Card details are not set"))
                    return {
                        'error_message': True,
                        'message': "Card details are not set"
                    }
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

        if code.get('params').get('is_shop') == 1:
            if trans_id and trans_id.sale_order_ids and trans_id.sale_order_ids.partner_shipping_id:
                if not trans_id.sale_order_ids.partner_shipping_id.country_id or not trans_id.sale_order_ids.partner_shipping_id.zip or not trans_id.sale_order_ids.partner_shipping_id.state_id or not trans_id.sale_order_ids.partner_shipping_id.city or not trans_id.sale_order_ids.partner_shipping_id.street:
                    return {
                        'error_message': True,
                        'message': 'Address, City, State, Zip and Country Fields are not set. These are required for payments.'
                    }
                address.postal_code = trans_id.sale_order_ids.partner_shipping_id.zip
                address.country = trans_id.sale_order_ids.partner_shipping_id.country_id.name
                if not trans_id.sale_order_ids.partner_shipping_id.state_id.name == "Armed Forces Americas":
                    address.state = trans_id.sale_order_ids.partner_shipping_id.state_id.name
                address.city = trans_id.sale_order_ids.partner_shipping_id.city
                address.street_address_1 = trans_id.sale_order_ids.partner_shipping_id.street
                address.street_address_2 = trans_id.sale_order_ids.partner_shipping_id.street2

            elif trans_id.invoice_ids and trans_id.invoice_ids.partner_shipping_id:
                if not trans_id.invoice_ids.partner_shipping_id.country_id or not trans_id.invoice_ids.partner_shipping_id.state_id or not trans_id.invoice_ids.partner_shipping_id.city or not trans_id.invoice_ids.partner_shipping_id.street or not trans_id.invoice_ids.partner_shipping_id.zip:
                    return {
                        'error_message': True,
                        'message': 'Address, City, State, Zip and Country Fields are not set. These are required for payments.'
                    }
                address.postal_code = trans_id.invoice_ids.partner_shipping_id.zip
                address.country = trans_id.invoice_ids.partner_shipping_id.country_id.name
                if not trans_id.invoice_ids.partner_shipping_id.state_id.name == "Armed Forces Americas":
                    address.state = trans_id.invoice_ids.partner_shipping_id.state_id.name
                address.city = trans_id.invoice_ids.partner_shipping_id.city
                address.street_address_1 = trans_id.invoice_ids.partner_shipping_id.street
                address.street_address_2 = trans_id.invoice_ids.partner_shipping_id.street2
            else:
                if not partner.country_id or not partner.state_id or not partner.street or not partner.city or not partner.zip:
                    return {
                        'error_message': True,
                        'message': 'Address, City, State, Zip and Country Fields are not set. These are required for payments.'
                    }
                address.postal_code = partner.zip if partner else None
                address.country = partner.country_id.name if partner else None
                if not partner.state_id.name == "Armed Forces Americas":
                    address.state = partner.state_id.name if partner else None
                address.city = partner.city if partner else None
                address.street_address_1 = partner.street if partner else None
                address.street_address_2 = partner.street2 if partner else None

        elif code.get('params').get('is_card'):
            if not token.customer_city or not token.customer_zip or not token.customer_state_id or not token.customer_country_id or not token.customer_street:
                if trans_id.sale_order_ids:
                    trans_id.sale_order_ids.message_post(body=_(
                        "Website: The bluemaxpay transaction was unsuccessful : Address details not set"))
                return {
                    'error_message': True,
                    'message': 'Address, City, State, Zip and Country Fields are not set for this saved card. These are required for payments.'
                }
            address.postal_code = token.customer_zip
            address.country = token.customer_country_id.name
            if not token.customer_state_id.name == "Armed Forces Americas":
                address.state = token.customer_state_id.name
            address.city = token.customer_city
            address.street_address_1 = token.customer_street

        else:
            if not code.get('params').get('web_street') or not code.get('params').get('web_city') or not code.get('params').get('web_state') or not code.get('params').get('web_country') or not code.get('params').get('web_zip'):
                if trans_id.sale_order_ids:
                    trans_id.sale_order_ids.message_post(body=_(
                        "Website: The bluemaxpay transaction was unsuccessful : Address details not set"))
                return {
                    'error_message': True,
                    'message': 'Address, City, State, Zip and Country Fields are not set above. These are required for payments.'
                }
            address.postal_code = code.get('params').get('web_zip')
            address.country = code.get('params').get('web_country')
            if not code.get('params').get('web_state') == "Armed Forces Americas":
                address.state = code.get('params').get('web_state')
            address.city = code.get('params').get('web_city')
            address.street_address_1 = code.get('params').get('web_street')

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
                if code.get('params').get('is_shop') == 1:
                    card_save.customer_street = partner.street
                    card_save.customer_state_id = partner.state_id.id
                    card_save.customer_city = partner.city
                    card_save.customer_zip = partner.zip
                    card_save.customer_country_id = partner.country_id.id
                else:
                    card_save.customer_street = code.get('params').get('web_street')
                    card_save.customer_state_id = code.get('params').get('web_state_val')
                    card_save.customer_city = code.get('params').get('web_city')
                    card_save.customer_zip = code.get('params').get('web_zip')
                    card_save.customer_country_id = code.get('params').get('web_country_val')

                card.token = save_card.token

        if not code.get('params').get('is_card'):
            if code.get('params').get('address_save'):
                if not code.get('params').get('name_address_save'):
                    return {
                        'error_message': True,
                        'message': 'Enter "Name on Saved Address"'
                    }
                child_data = {
                    'type': 'other',
                    'name': code.get('params').get('name_address_save'),
                    'street': code.get('params').get('web_street'),
                    'state_id': code.get('params').get('web_state_val'),
                    'city': code.get('params').get('web_city'),
                    'zip': code.get('params').get('web_zip'),
                    'country_id': code.get('params').get('web_country_val'),
                }
                if trans_id.sale_order_ids.partner_shipping_id:
                    trans_id.sale_order_ids.partner_shipping_id.write({
                        'child_ids': [(0, 0, child_data)]
                    })
                elif trans_id.invoice_ids.partner_shipping_id:
                    trans_id.invoice_ids.partner_shipping_id.write({
                        'child_ids': [(0, 0, child_data)]
                    })
                else:
                    partner.write({
                        'child_ids': [(0, 0, child_data)]
                    })

        if payment_type == 'capture':
            try:
                response = card.authorize(float(code.get('params').get('amount'))) \
                    .with_currency(request.env.user.currency_id.name) \
                    .with_address(address) \
                    .execute()
                if response.response_code != '00':
                    if trans_id.sale_order_ids:
                        trans_id.sale_order_ids.message_post(body=_(
                            "Gateway: The bluemaxpay transaction was unsuccessful : %s Please Check your Credentials and Cards details." % (response.response_message)))
                    return {
                        'error_message': True,
                        'message':  "{} : Please Check your Credentials and Cards details.".format(response.response_message)
                    }
                Transaction.from_id(
                    response.transaction_reference.transaction_id) \
                    .capture(float(code.get('params').get('amount'))) \
                    .execute()

            except ApiException as e:
                if trans_id.sale_order_ids:
                    trans_id.sale_order_ids.message_post(body=_(
                        "Website: The bluemaxpay transaction was unsuccessful : Please Check your Card details."))
                return {
                    'error_message': True,
                    'message': "Please Check your Card details."
                }
        elif payment_type == 'authorize':
            try:
                response = card.authorize(code.get('params').get('amount')) \
                    .with_currency(request.env.company.currency_id.name) \
                    .with_address(address) \
                    .execute()
                if response.response_code != '00':
                    if trans_id.sale_order_ids:
                        trans_id.sale_order_ids.message_post(body=_(
                            "Gateway: The bluemaxpay transaction was unsuccessful : %s Please Check your Credentials and Cards details." % (response.response_message)))
                    return {
                        'error_message': True,
                        'message':  "{} : Please Check your Credentials and Cards details.".format(response.response_message)
                    }

            except ApiException as e:
                if trans_id.sale_order_ids:
                    trans_id.sale_order_ids.message_post(body=_(
                        "Website: The bluemaxpay transaction was unsuccessful : Please Check your Card details."))
                return {
                    'error_message': True,
                    'message':  "Please Check your Card details."
                }
        if response.response_code != '00':
            if trans_id.sale_order_ids:
                trans_id.sale_order_ids.message_post(body=_(
                    "Gateway: The bluemaxpay transaction was unsuccessful : %s Please Check your Credentials and Cards details." % (response.response_message)))
            return {
                'error_message': True,
                'message':  "{} : Please Check your Credentials and Cards details.".format(response.response_message)
            }

        bluemaxpay_trans = request.env['bluemaxpay.transaction'].sudo().create({
            'name': trans_id.sale_order_ids.name if trans_id.sale_order_ids else trans_id.invoice_ids.name,
            'amount': code.get('params').get('amount'),
            'partner_id': partner.id,
            'date': fields.Datetime.now(),
            'sale_id': trans_id.sale_order_ids.id if not trans_id.invoice_ids else None,
            'move_id': trans_id.invoice_ids.id if trans_id.invoice_ids and len(trans_id.invoice_ids) == 1 else None,
            'move_ids': [(6, 0, trans_id.invoice_ids.ids)] if trans_id.invoice_ids and len(trans_id.invoice_ids) > 0 else None,
            'transaction_id': trans_id.id,
            'payment_type': payment_type,
            'currency_id': request.env.company.currency_id.id,
        })

        if trans_id.sale_order_ids:
            address_details = ''
            address_details += f" Street : {address.street_address_1} , City : {address.city} , State : {address.state} , Zip code : {address.postal_code} , Country : {address.country}"
            trans_id.sale_order_ids.paymentlink_address_note = address_details
            trans_id.sale_order_ids.paymentlink_card_name = code.get('params').get('name') or f"Saved card: {partner.name}"
            trans_id.sale_order_ids.paymentlink_customer_ip = request.httprequest.environ.get(
                'REMOTE_ADDR')
            trans_id.sale_order_ids.get_geolocation(request.httprequest.environ.get(
                'REMOTE_ADDR'))
            trans_id.sale_order_ids.is_payment_link_paid = True

            if code.get('params').get('is_shop') != 1:
                notification_msg = f"Sale Order '{trans_id.sale_order_ids.name}' has been paid via a web link successfully using Bluemax Pay. Customer : '{partner.name}'. Amount : '{code.get('params').get('amount')}'."
                salesperson = trans_id.sale_order_ids.user_id
                channel_id = request.env['discuss.channel'].sudo().search([('name', 'ilike', 'OdooBot')])
                if channel_id:
                    channel_id[0].message_post(
                        body=(notification_msg),
                        message_type='notification',
                        partner_ids= [salesperson.id for user in salesperson if salesperson],
                    )

        if response.response_code == '00':
            if bluemaxpay_trans.response_log:
                bluemaxpay_trans.response_log += f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"
            else:
                bluemaxpay_trans.response_log = f"\n{response.__dict__}\n{response.transaction_reference.__dict__}\n{response.transaction_reference.payment_method_type.__dict__}\n---------------------------------------------------\n"

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
