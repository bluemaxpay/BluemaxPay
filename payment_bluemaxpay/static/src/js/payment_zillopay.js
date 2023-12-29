odoo.define('payment_bluemaxpay.payment_bluemaxpay', require => {
    'use strict';
    const publicWidget = require('web.public.widget');

    publicWidget.registry.PaymentBlueMaxPay = publicWidget.Widget.extend({

        selector: '.card_form_details',
        events: {
            'change': '_onChange',
        },
        _onChange: function() {
            // debugger
            var is_card = $('#is_card').is(":checked");
            if (is_card == true) {
                var card = document.getElementById('bluemaxpay-token')
                var card_number = document.getElementById('card_number')
                var card_name = document.getElementById('card_name')
                var card_exp_month = document.getElementById('card_exp_month')
                var card_exp_year = document.getElementById('card_exp_year')
                var card_code = document.getElementById('card_code')
                var card_number = document.getElementById('card_number')
                var save = document.getElementById('is-card-save')
                save.classList.add('d-none')
                card_number.classList.add('d-none')
                card_name.classList.add('d-none')
                card_exp_month.classList.add('d-none')
                card_exp_year.classList.add('d-none')
                card_code.classList.add('d-none')
                card.classList.remove('d-none')
            } else {
                var card = document.getElementById('bluemaxpay-token')
                var card_number = document.getElementById('card_number')
                var card_name = document.getElementById('card_name')
                var card_exp_month = document.getElementById('card_exp_month')
                var card_exp_year = document.getElementById('card_exp_year')
                var card_code = document.getElementById('card_code')
                var save = document.getElementById('is-card-save')
                save.classList.remove('d-none')
                card_number.classList.remove('d-none')
                card_name.classList.remove('d-none')
                card_exp_month.classList.remove('d-none')
                card_exp_year.classList.remove('d-none')
                card_code.classList.remove('d-none')
                card.classList.add('d-none')
            }
        }
    });
});