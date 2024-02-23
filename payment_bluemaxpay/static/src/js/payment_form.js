/** @odoo-module **/

import paymentForm from '@payment/js/payment_form';
import { jsonrpc } from "@web/core/network/rpc_service";
import { _t } from "@web/core/l10n/translation";
import { Component } from '@odoo/owl';


paymentForm.include({
    async start() {
        this.paymentContext = {};
        Object.assign(this.paymentContext, this.el.dataset);

        // await this._super(...arguments);
        // Expand the payment form of the selected payment option if there is only one.
        const checkedRadio = document.querySelector('input[name="o_payment_radio"]:checked');
        if (checkedRadio) {
            await this._expandInlineForm(checkedRadio);
            this._enableButton(false);
        } else {
            this._setPaymentFlow(); // Initialize the payment flow to let providers overwrite it.
        }
        this.$('[data-bs-toggle="tooltip"]').tooltip();
        Component.env.bus.addEventListener('update_shipping_cost', (ev) => this._updateShippingCost(ev.detail));
        const submitButton = document.querySelector('[name="o_payment_submit_button"]');
        if (submitButton != null) {
            submitButton.addEventListener('click', ev => this._submitForm(ev));
        }
    },

    _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'bluemaxpay') {
            return this._super(...arguments);
        }
        console.log('asdfs', providerCode)
        console.log('acqu', processingValues.provider_id)
        console.log('proc', processingValues)
        const card_name = document.getElementById('card-name').value;
        const card_number = document.getElementById('card-number').value;
        const exp_year = document.getElementById('card-exp-year').value;
        const exp_month = document.getElementById('card-exp-month').value;
        const card_code = document.getElementById('card-code').value;

        const webStreetElement = document.getElementById('web-street');
        const webCityElement = document.getElementById('web-city');

        const web_street = webStreetElement ? webStreetElement.value : '';
        const web_city = webCityElement ? webCityElement.value : '';

        const webStateElement = document.getElementById('web-state');
        const webCountryElement = document.getElementById('web-country');

        const web_state = webStateElement ? webStateElement.options[webStateElement.selectedIndex].text.trim() : '';
        const web_country = webCountryElement ? webCountryElement.options[webCountryElement.selectedIndex].text.trim() : '';

        const webZipElement = document.getElementById('web-zip');

        const web_zip = webZipElement ? webZipElement.value : '';
        const NameSavedAddress = document.getElementById('name-save-address');

        const save_address_check = $('#is_address_save').is(":checked");
        const name_save_address = NameSavedAddress ? NameSavedAddress.value : '';

        // check if payment is made from website shop(1) or payment link (0)
        var is_shop = 0
        if ($('#payment_address_hidden')[0] == null) {
            is_shop = 1
        } else {
            is_shop = 0
        }

        var is_card = $('#is_card').is(":checked");
        var card = document.getElementById('token')
        console.log(card, 'aaaaaaaa')
        if (is_card == true) {
            console.log('inside card value')
            if (card.value == '') {
                self._displayErrorDialog(
                    _t("Validation Error"),
                    _t("Please add a valid card")
                );
            }
        } else {
            console.log('Else card value')
            if (save_address_check == true) {
                if (name_save_address == '') {
                    self._displayErrorDialog(
                        _t("Missing Required Fields"),
                        _t("Please Enter 'Name On Saved Address'")
                    );
                }
            }
            if (card_number == '') {
                self._displayErrorDialog(
                    _t("Validation Error"),
                    _t("Please add a valid card number")
                );
            }
            if (exp_month == '') {
                self._displayErrorDialog(
                    _t("Validation Error"),
                    _t("Please add a valid card expiration month")
                );
            }
            if (exp_year == '') {
                self._displayErrorDialog(
                    _t("Validation Error"),
                    _t("Please add a valid card expiration year")
                );
            }
            if (card_code == '') {
                self._displayErrorDialog(
                    _t("Validation Error"),
                    _t("Please add a valid cvv")
                );
            }
            if (card_name == '') {
                self._displayErrorDialog(
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
        jsonrpc("/get_bluemaxpay/order", {}).then(function(sale) {
            console.log('order', sale)
            jsonrpc('/bluemaxpay/transaction', {
                model: 'payment.transaction',
                params: {
                    'name': card_name,
                    'number': card_number,
                    'exp_year': exp_year,
                    'exp_month': exp_month,
                    'card_code': card_code,
                    'card': card.value,
                    'is_shop': is_shop,
                    'is_card': is_card || false,
                    'card_save': save_card_check || false,
                    'address_save': save_address_check || false,
                    'name_address_save': name_save_address,
                    'code': processingValues.provider_id,
                    'sale': sale.sale_order_id,
                    'trans_id': sale.trans_id,
                    'web_street': web_street,
                    'web_city': web_city,
                    'web_state': web_state,
                    'web_country': web_country,
                    'web_state_val': webStateElement ? parseInt(webStateElement.value.trim()) : null,
                    'web_country_val': webCountryElement ? parseInt(webCountryElement.value.trim()) : null,
                    'web_zip': web_zip,
                    'is_invoice': sale.is_invoice,
                    'amount': amount,
                    'currency': currency,
                    'partner': partner
                }
            }).then(function(result) {
                console.log('res', result)
                if (result.error_message == true) {
                    console.log(self, 'test aaa')
                    self._displayErrorDialog(
                        _t("Validation Error"),
                        _t(result.message)
                    );
                }
                if (result.error_message == false) {
                    jsonrpc('/payment/bluemaxpay/transaction/return', {
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

    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'bluemaxpay') {
            return this._super(...arguments);
        } else if (flow === 'token') {
            return Promise.resolve();
        }
        this._setPaymentFlow('direct');
        return Promise.resolve()
    }
});