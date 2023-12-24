# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request


class PosBluemax(http.Controller):

    def _get_card_type(self, card_number):
        card_types = {
            "Visa": ["4"],
            "MasterCard": ["51", "52", "53", "54", "55"],
            "American Express": ["34", "37"],
            "Discover": ["6011", "644", "645", "646", "647", "648", "649", "65"],
            "Diners Club": ["300", "301", "302", "303", "304", "305", "36", "38"]
        }

        first_four_digits = card_number[:4]

        for card, prefixes in card_types.items():
            for prefix in prefixes:
                if first_four_digits.startswith(prefix):
                    return card
        return ""

    @http.route('/pos/payment/bluemax', type="http", auth="public", methods=['POST'], csrf=False)
    def fetch_bluemax_data(self, **kw):
        txid = kw.get('txid')
        bluemax_payment = request.env['bluemax.pos.payment'].browse(int(txid))

        kw.update({
            "transactionId": kw.get("transactionId") if kw.get("transactionId") != 'null' else '',
            "cardholderName": kw.get("cardholderName") if kw.get("cardholderName") != 'null' else '',
            "deviceResponseCode": kw.get("deviceResponseCode") if kw.get("deviceResponseCode") != 'null' else '',
            "deviceResponseMessage": kw.get("deviceResponseMessage") if kw.get("deviceResponseMessage") != 'null' else '',
            "responseText": kw.get("responseText") if kw.get("responseText") != 'null' else '',
            "maskedCardNumber": kw.get("maskedCardNumber") if kw.get("maskedCardNumber") != 'null' else '',
            "transactionAmount": kw.get("transactionAmount") if kw.get("transactionAmount") != 'null' else '',
            "approvedAmount": kw.get("approvedAmount") if kw.get("approvedAmount") != 'null' else '',
            "applicationName": kw.get("applicationName") if kw.get("applicationName") != 'null' else '',
            "applicationId": kw.get("applicationId") if kw.get("applicationId") != 'null' else '',
            "terminalRefNumber": kw.get("terminalRefNumber") if kw.get("terminalRefNumber") != 'null' else '',
            "approvalcode": kw.get("approvalcode") if kw.get("approvalcode") != 'null' else '',
            "entrymode": kw.get("Entrymode") if kw.get("Entrymode") != 'null' else '',
            "card_type": self._get_card_type(kw.get("maskedCardNumber")) if kw.get("maskedCardNumber") != 'null' else ''
        })

        bluemax_payment.sudo().write({
            "state": kw.get('status'),
            "transactionId": kw.get("transactionId"),
            "cardholderName": kw.get("cardholderName"),
            "deviceResponseCode": kw.get("deviceResponseCode"),
            "deviceResponseMessage": kw.get("deviceResponseMessage"),
            "responseText": kw.get("responseText"),
            "maskedCardNumber": kw.get("maskedCardNumber"),
            "transactionAmount": kw.get("transactionAmount"),
            "approvedAmount": kw.get("approvedAmount"),
            "applicationName": kw.get("applicationName"),
            "applicationId": kw.get("applicationId")
        })

        message = "Payment Failed"
        if bluemax_payment.state == 'success':
            message = "Payment Successful"

        session = request.env['pos.session'].sudo().search(
            [('state', '=', 'opened'), ('user_id', '=', int(kw.get('uid')))], limit=1)

        kw.update({
            'user_id': session.user_id.id,
            'message': message,
        })

        request.env['bus.bus'].sudo()._sendmany([[
            session.user_id.partner_id, 'bluemax.pos.payment.channel', {
                'payment_response': kw}
        ]])

        return request.make_response(
            json.dumps({'status': 'success'}),
            headers=[("Content-Type", "application/json")]
        )
