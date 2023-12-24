odoo.define('pos_bluemax.payment_bluemax', function (require) {
"use strict";

const core = require('web.core');
const rpc = require('web.rpc');
const PaymentInterface = require('point_of_sale.PaymentInterface');
const { Gui } = require('point_of_sale.Gui');
const utils = require('web.utils');

const _t = core._t;

let PaymenteBluemax = PaymentInterface.extend({

    send_payment_request: async function (cid) {
        await this._super.apply(this, arguments);
        let line = this.pos.get_order().selected_paymentline;
        let order = this.pos.get_order();
        line.set_payment_status('waiting');

        let txid = await this.createTransaction({
            'amount': line.amount,
            'order_id': order.uid,
            'currency_id': this.pos.currency.name,
            'payment_method_id': line.payment_method.id
        });

        window.location.href = `intent://bluemax?amount=${line.amount}&currency=${this.pos.currency.name}&reference=${order.uid}&txid=${txid}&uid=${this.pos.pos_session.user_id[0]}&return_url=${this.pos.base_url}/pos/payment/bluemax#Intent;scheme=bluemax;package=com.BlueMaxPayC2X.app;end;`;
    },

    createTransaction: async function (tx_data) {
        let data = await rpc.query({
            model: 'bluemax.pos.payment',
            method: 'create_bluemax_payment',
            args: [[], tx_data],
        }, {
            silent: true,
        });
        return data;
    },

    bluemax_validate: async function (payment_response) {
        let order = this.pos.get_order();
        let line = order.selected_paymentline; 

        if (payment_response.status == 'success') {
            line.bluemax_data = true;
            line.transaction_id = payment_response.transactionId || '';
            line.cardholder_name = payment_response.cardholderName || '';
            line.entrymode = payment_response.Entrymode || '';
            line.card_number = payment_response.maskedCardNumber || '';
            line.card_type = this._get_card_type(payment_response.maskedCardNumber) || '';
            line.bluemaxpay_response = payment_response.deviceResponseCode || '';
            line.approved_amount = payment_response.approvedAmount || 0.00;
            line.ref_number = payment_response.terminalRefNumber || '';
            line.auth_code = payment_response.approvalcode || '';

            line.set_payment_status('done');
        } else {
            this._showError("ERROR", "FAILED");
            line.set_payment_status('retry');
        }
    },

    _get_card_type(cardNumber) {
        const cardTypes = {
            "Visa": ["4"],
            "MasterCard": ["51", "52", "53", "54", "55"],
            "American Express": ["34", "37"],
            "Discover": ["6011", "644", "645", "646", "647", "648", "649", "65"],
            "Diners Club": ["300", "301", "302", "303", "304", "305", "36", "38"]
        };

        const firstFourDigits = cardNumber.substring(0, 4);

        for (const [card, prefixes] of Object.entries(cardTypes)) {
            for (const prefix of prefixes) {
                if (firstFourDigits.startsWith(prefix)) {
                    return card;
                }
            }
        }

        return "";
    },

    send_payment_cancel: async function (order, cid) {
        /**
         * Override
         */
        this._super.apply(this, arguments);
        let line = this.pos.get_order().selected_paymentline;
        line.set_payment_status('retry');
        return true;
    },

    _showError: function (msg, title) {
        if (!title) {
            title =  _t('Bluemax Error');
        }
        Gui.showPopup('ErrorPopup',{
            'title': title,
            'body': msg,
        });
    },
});

return PaymenteBluemax;
});
