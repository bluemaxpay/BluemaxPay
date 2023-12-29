/** @odoo-module */
/* global BluemaxTerminal */

import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";

export class PaymentBluemax extends PaymentInterface {

    async createTransaction(tx_data) {
        return await this.env.services.orm.silent.call(
            "bluemax.pos.payment",
            "create_bluemax_payment",
            [[], tx_data]
        );
    }

    async bluemax_validate(payment_response) {
        const order = this.pos.get_order();
        const line = order.selected_paymentline; 

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
    }

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
    }

    async send_payment_request(cid) {
        /**
         * Override
         */
        await super.send_payment_request(...arguments);
        const order = this.pos.get_order();
        const line = this.pos.get_order().selected_paymentline;
        line.set_payment_status("waiting");
        try {
            let txid = await this.createTransaction({
                'amount': line.amount,
                'order_id': order.uid,
                'currency_id': this.pos.currency.name,
                'payment_method_id': line.payment_method.id
            });
            window.location.href = `intent://bluemax?amount=${line.amount}&currency=${this.pos.currency.name}&reference=${order.uid}&txid=${txid}&uid=${this.pos.pos_session.user_id[0]}&return_url=${this.pos.base_url}/pos/payment/bluemax#Intent;scheme=bluemax;package=com.BlueMaxPayC2X.app;end;`;
        } catch (error) {
            this._showError(error);
            return false;
        }
    }

    async send_payment_cancel(order, cid) {
        /**
         * Override
         */
        super.send_payment_cancel(...arguments);
        const line = this.pos.get_order().selected_paymentline;
        line.set_payment_status("retry");
        return true;
    }

    // private methods

    _showError(msg, title) {
        if (!title) {
            title = _t("Bluemax Error");
        }
        this.env.services.popup.add(ErrorPopup, {
            title: title,
            body: msg,
        });
    }
}
