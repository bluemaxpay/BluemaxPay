odoo.define('pos_card_not_present.CardNotPresentZilloPayPayment', function(require) {
    'use strict';
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const PosComponent = require('point_of_sale.PosComponent');
    const ControlButtonsMixin = require('point_of_sale.ControlButtonsMixin');
    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const { useListener } = require("@web/core/utils/hooks");
    const { onChangeOrder, useBarcodeReader } = require('point_of_sale.custom_hooks');
    const { useState } = owl;
    const { Gui } = require('point_of_sale.Gui');
    var rpc = require('web.rpc');
    var core = require('web.core');

    var _t = core._t;

    class CardNotPresentZilloPayPayment extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            this.state = useState({
                number: this.props.number,
                year: this.props.year,
                month: this.props.month,
                cvv: this.props.cvv,
                token: '',
                name: this.props.name,
                order: this.env.pos.get_order().selected_paymentline
            });
            console.log(this.env.pos, 'order')
        }
        async confirm() {
            console.log('confirm', this.env.pos.get_order(), )
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            var order = this.env.pos.get_order()
            var amount = order.selected_paymentline.amount
            var payload = JSON.parse(this.getPayload())
            var result = await this.rpc({
                model: 'pos.payment.method',
                method: 'payment_card_not_present',
                args: [this.props.payment_method, payload, amount]
            });

            if (result.response_code == '00') {
                console.log('***** payment *** Response', result)
                order.selected_paymentline.set_payment_status('done');
                console.log(this.selectedPaymentLine)
                order.selected_paymentline.card_type = result.card_type;
                order.selected_paymentline.cardholder_name = this.props.name;
                order.selected_paymentline.card_number = '******' + this.props.number.slice(-4);
                order.selected_paymentline.transaction_id = result.transaction_id;
                order.selected_paymentline.approved_amount = amount;
                order.selected_paymentline.zillo_response = result.response_message;
                order.selected_paymentline.ref_number = result.reference_number;
                order.selected_paymentline.auth_code = result.auth_code;
                order.selected_paymentline.avs_resp = result.avs_response_message;
                this.env.posbus.trigger('close-popup', {
                    popupId: this.props.id,
                    response: { confirmed: false, payload: null },
                });
            }
            if (result.response_code != '00') {
                if (result.response_message) {
                    console.log(result, 'resss');
                    this.showPopup("ErrorPopup", {
                        'title': ("Connection Error"),
                        'body': (result.response_message)
                    });
                } else {
                    console.log(result, 'resss');
                    this.showPopup("ErrorPopup", {
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
            var order = this.env.pos.get_order().selected_paymentline
            if (token.value == "" || token == '') {
                if (this.props.name && this.props.number && this.props.cvv && this.props.year && this.props.month) {
                    console.log('Card data')
                } else {
                    this.showPopup("ErrorPopup", {
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
    CardNotPresentZilloPayPayment.template = 'CardNotPresentZilloPayPayment';
    CardNotPresentZilloPayPayment.defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'ZilloPay Payment',
        body: '',
    };
    Registries.Component.add(CardNotPresentZilloPayPayment);
    return CardNotPresentZilloPayPayment;
});