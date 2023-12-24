/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { PosStore } from "@point_of_sale/app/store/pos_store";
const { useState } = owl;
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(loadedData);
        this.bluemaxpay = loadedData['bluemax.token'];
        this.pos_payment_data = loadedData['pos.payment'];
        this.number = '';
        this.year = '';
        this.month = '';
        this.cvv = '';
        this.name = ''
    }
});

export class CardNotPresentBlueMaxPayPayment extends AbstractAwaitablePopup {
    static template = "CardNotPresentBlueMaxPayPayment";
    static defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'BlueMax Pay Payment',
        body: '',
    };

    constructor() {
        super(...arguments);
        this.state = useState({
            number: this.props.number,
            year: this.props.year,
            month: this.props.month,
            cvv: this.props.cvv,
            token: this.props.token,
            name: this.props.name,
            order: this.props.order.selected_paymentline,
        });
        console.log(this.props.order, 'order')
    }
    async confirm() {
        console.log('confirm', this.props.order, )
        this.props.resolve({ confirmed: true, payload: await this.getPayload() });
        var order = this.props.order
        var amount = order.selected_paymentline.amount
        var payload = JSON.parse(this.getPayload())
        var result = await this.env.services.orm.silent.call(
            'pos.payment.method',
            'payment_card_not_present',
            [this.props.payment_method, payload, amount]
        );
        if (result.response_code == '00') {
            console.log('***** payment *** Response', result)
            order.selected_paymentline.set_payment_status('done');
            console.log(this.selectedPaymentLine)
            order.selected_paymentline.card_type = result.card_type;
            order.selected_paymentline.cardholder_name = this.props.name;
            order.selected_paymentline.card_number = '******' + this.props.number.slice(-4);
            order.selected_paymentline.transaction_id = result.transaction_id;
            order.selected_paymentline.approved_amount = amount;
            order.selected_paymentline.bluemaxpay_response = result.response_message;
            order.selected_paymentline.ref_number = result.reference_number;
            order.selected_paymentline.auth_code = result.auth_code;
            order.selected_paymentline.avs_resp = result.avs_response_message;
            this.props.close({ confirmed: false, payload: null });
        }
        if (result.response_code != '00') {
            if (result.response_message) {
                console.log(result, 'resss');
                this.env.services.popup.add(ErrorPopup, {
                    'title': ("Connection Error"),
                    'body': (result.response_message)
                });
            } else {
                console.log(result, 'resss');
                this.env.services.popup.add(ErrorPopup, {
                    'title': ("Connection Error"),
                    'body': (result)
                });
            }

        }
        console.log(result, "res...")
        console.log(order, "res...")
        order.stop_electronic_payment();
    }
    _onChange() {
        console.log('_onChange')
        var token = ''
        console.log(token.value, 'aaaa')
        if (token.value == "") {
            $('#card-holder-name').show()
            $('#card-cvv').show()
            $('#card-number').show()
            $('#card-year').show()
            $('#card-month').show()
        } else {
            $('#card-holder-name').hide()
            $('#card-cvv').hide()
            $('#card-number').hide()
            $('#card-year').hide()
            $('#card-month').hide()
        }
    }
    getPayload() {
        console.log(this.state, 'eeeee')
        var token = document.getElementById('bluemaxpay-token')
        var card_name = document.getElementById('card_name')
        var card_number = document.getElementById('card_number')
        var card_month = document.getElementById('card_month')
        var card_year = document.getElementById('card_year')
        var card_cvv = document.getElementById('card_cvv')
        console.log(card_name, card_number)
        var order = this.props.order.selected_paymentline

        if (token.value == "" || token == '') {
            if (this.props.name && this.props.number && this.props.cvv && this.props.year && this.props.month) {
                console.log('Card data')
            } else {
                this.env.services.popup.add(ErrorPopup, {
                    'title': ("Invalid Card Details!"),
                    'body': ("Add all details for the card")
                });
            }
            var payload = {
                is_token: false,
                name: card_name.value,
                number: card_number.value,
                year: card_year.value,
                month: card_month.value,
                cvv: card_cvv.value,
            }
            return JSON.stringify(payload)
        } else {

            var payload = {
                is_token: true,
                token: token.value,
            }
            return JSON.stringify(payload)
        }
    }

}