odoo.define('payment_bluemaxpay.payment_form', require => {
    'use strict';

    const core = require('web.core');
    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');
    const PaymentMixin = require('payment.payment_form_mixin');
    var rpc = require('web.rpc');
    const ajax = require('web.ajax');
    const _t = core._t;

    const paymentBlueMaxPayMixin = {
        _processDirectPayment: function(code, acquirerId, processingValues) {
            // debugger;
            if (code !== 'bluemaxpay') {
                return this._super(...arguments);
            }
            console.log('asdfs', code)
            console.log('acqu', acquirerId)
            console.log('proc', processingValues)
            // debugger;
            const card_name = document.getElementById('card-name').value;
            const card_number = document.getElementById('card-number').value;
            const exp_year = document.getElementById('card-exp-year').value;
            const exp_month = document.getElementById('card-exp-month').value;
            const card_code = document.getElementById('card-code').value;
            var is_card = $('#is_card').is(":checked");
            var card = document.getElementById('token')
            console.log(card, 'aaaaaaaa')
            if (is_card == true) {
                console.log('inside card value')
                if (card.value == '') {
                    this._displayError(
                        _t("Validation Error"),
                        _t("Please add a valid card")
                    );
                }
            } else {
                console.log('Else card value')
                if (card_number == '') {
                    this._displayError(
                        _t("Validation Error"),
                        _t("Please add a valid card number")
                    );
                }
                if (exp_month == '') {
                    this._displayError(
                        _t("Validation Error"),
                        _t("Please add a valid card expiration month")
                    );
                }
                if (exp_year == '') {
                    this._displayError(
                        _t("Validation Error"),
                        _t("Please add a valid card expiration year")
                    );
                }
                if (card_code == '') {
                    this._displayError(
                        _t("Validation Error"),
                        _t("Please add a valid cvv")
                    );
                }
                if (card_name == '') {
                    this._displayError(
                        _t("Validation Error"),
                        _t("Please add a card holder name")
                    );
                }
            }
            const amount = processingValues.amount;
            const currency = processingValues.currency_id;
            const partner = processingValues.partner_id;
            const save_card_check = $('#is_card_save').is(":checked");
            var self = this;
            ajax.jsonRpc("/get_bluemaxpay/order", 'call', {}).then(function(sale) {
                // debugger;
                console.log('order', sale)
                rpc.query({
                    route: '/bluemaxpay/transaction',
                    model: 'payment.transaction',
                    params: {
                        'name': card_name,
                        'number': card_number,
                        'exp_year': exp_year,
                        'exp_month': exp_month,
                        'card_code': card_code,
                        'card': card.value,
                        'is_card': is_card || false,
                        'card_save': save_card_check || false,
                        'code': acquirerId,
                        'sale': sale.sale_order_id,
                        'trans_id': sale.trans_id,
                        'is_invoice': sale.is_invoice,
                        'amount': amount,
                        'currency': currency,
                        'partner': partner
                    }
                }).then(function(result) {
                    console.log('res', result)
                    if (result.error_message == true) {
                        console.log(self, 'test aaa')
                        self._displayError(
                            _t("Validation Error"),
                            _t(result.message)
                        );
                    }
                    if (result.error_message == false) {
                        rpc.query({
                            route: '/payment/bluemaxpay/transaction/return',
                            params: {
                                'reference': processingValues.reference,
                                'bluemaxpay_transaction': result.bluemaxpay_trans
                            },
                        }).then((eee) => {
                            console.log('eeee', eee)
                            window.location = '/payment/status';
                        });
                    }
                });
            });
        },

        _prepareInlineForm: function(code, paymentOptionId, flow) {
            if (code !== 'bluemaxpay') {
                return this._super(...arguments);
            } else if (flow === 'token') {
                return Promise.resolve();
            }
            this._setPaymentFlow('direct');
            return Promise.resolve()
        },
    };
    checkoutForm.include(paymentBlueMaxPayMixin);
    manageForm.include(paymentBlueMaxPayMixin);
});