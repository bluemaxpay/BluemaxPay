/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.PaymentBlueMaxPay = publicWidget.Widget.extend({

        start: function() {
            this._super.apply(this, arguments);
            this._showDefaultAddressData();
            this._onChange();
            return this;
        },
        selector: '.card_form_details',
        events: {
            'change': '_onChange',
            'change #saved_addresses': '_onChangeSavedAddress',
        },
        _onChangeSavedAddress: function(ev) {
            const savedAddressId = $(ev.currentTarget).val();
            if (savedAddressId) {
                this._fetchSavedAddressData(savedAddressId);
            } else {
                this._showDefaultAddressData();
            }
        },
        _fetchSavedAddressData: function(savedAddressId) {
            jsonrpc(
                'res.partner',
                'read',
                [
                    [parseInt(savedAddressId)],
                    ['street', 'city', 'state_id', 'country_id', 'zip']
                ]
            ).then(data => {
                const partnerData = data[0];
                this._updateInputFields(partnerData);
            });
        },
        _showDefaultAddressData: function() {
            this._updateStateCountry($('#payment_address_hidden_state'), $('#payment_address_hidden_country'));
            jsonrpc(
                'res.partner',
                'read',
                [
                    [parseInt($('#payment_address_hidden').val())],
                    ['street', 'city', 'state_id', 'country_id', 'zip']
                ]
            ).then(data => {
                const parentPartnerData = data[0];
                this._updateInputFields(parentPartnerData);
            });
        },
        _updateStateCountry: function(state, country) {
            $('#web-state').val(parseInt(state.val()) || '');
            $('#web-country').val(parseInt(country.val()) || '');
        },
        _updateInputFields: function(partnerData) {
            $('#web-street').val(partnerData.street || '');
            $('#web-city').val(partnerData.city || '');
            $('#web-state').val(partnerData.state_id[0] || '');
            $('#web-country').val(partnerData.country_id[0] || '');
            $('#web-zip').val(partnerData.zip || '');
        },
        _onChange: function() {
            var is_card = $('#is_card').is(":checked");
            var card = document.getElementById('bluemaxpay-token');
            var card_number = document.getElementById('card_number');
            var card_name = document.getElementById('card_name');
            var card_exp_month = document.getElementById('card_exp_month');
            var card_exp_year = document.getElementById('card_exp_year');
            var card_code = document.getElementById('card_code');
            var save = document.getElementById('is-card-save');
            var address_save = document.getElementById('is-address-save');

            var web_street = document.getElementById('web_street');
            var web_city = document.getElementById('web_city');
            var web_state = document.getElementById('web_state');
            var web_country = document.getElementById('web_country');
            var web_zip = document.getElementById('web_zip');
            var web_hr = document.getElementById('web_hr');
            var saved_addresses = document.getElementById('bluemaxpay-saved-addresses');
            var name_address = document.getElementById('name_save_address');

            if (is_card == true) {
                hideElement(web_street);
                hideElement(web_city);
                hideElement(web_state);
                hideElement(web_country);
                hideElement(web_zip);
                hideElement(web_hr);
                hideElement(saved_addresses);
                hideElement(save);

                hideElement(address_save);
                hideElement(card_number);
                hideElement(card_name);
                hideElement(card_exp_month);
                hideElement(card_exp_year);
                hideElement(card_code);
                hideElement(name_address);
                
                showElement(card);
            } else {
                if ($('#is_address_save').is(":checked") == true) {
                    showElement(name_address);
                    $('#is_address_save').prop('required', true);
                } else {
                    hideElement(name_address);
                    $('#is_address_save').prop('required', false);
                }
                showElement(web_street);
                showElement(web_city);
                showElement(web_state);
                showElement(web_country);
                showElement(web_zip);
                showElement(web_hr);
                showElement(saved_addresses);
                showElement(save);
                showElement(address_save);

                showElement(card_number);
                showElement(card_name);
                showElement(card_exp_month);
                showElement(card_exp_year);
                showElement(card_code);
                hideElement(card);
            }
        }
    });

    function hideElement(element) {
        if (element) {
            element.classList.add('d-none');
        }
    }

    function showElement(element) {
        if (element) {
            element.classList.remove('d-none');
        }
    }
