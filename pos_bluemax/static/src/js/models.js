odoo.define('pos_bluemax.models', function(require) {
    var PaymentBluemax = require('pos_bluemax.payment_bluemax');
    var PaymentBlueMaxPayPay = require('pos_bluemax.payment');
    const { register_payment_method, Payment } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');

    register_payment_method('bluemax', PaymentBluemax);
    register_payment_method('savedcards', PaymentBlueMaxPayPay);

    const PosBluemaxPaymentLine = (Payment) => class PosBluemaxPaymentLine extends Payment {
        constructor(obj, options) {
            super(...arguments);
            this.bluemax_data = false;
            this.entrymode = '';
            this.card_type = '';
            this.card_number = '';
            this.bluemaxpay_response = '';
            this.approved_amount = 0.00;
            this.ref_number = '';
            this.auth_code = '';
        }
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.bluemax_data = json.bluemax_data || false;
            this.entrymode = json.entrymode || '';
            this.card_type = json.card_type || '';
            this.card_number = json.card_number || '';
            this.bluemaxpay_response = json.bluemaxpay_response || '';
            this.approved_amount = json.approved_amount || 0.00;
            this.ref_number = json.ref_number || '';
            this.auth_code = json.auth_code || '';
        }
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.bluemax_data = this.bluemax_data || false;
            json.entrymode = this.entrymode || '';
            json.card_type = this.card_type || '';
            json.card_number = this.card_number;
            json.bluemaxpay_response = this.bluemaxpay_response || '';
            json.approved_amount = this.approved_amount || 0.00;
            json.ref_number = this.ref_number || '';
            json.auth_code = this.auth_code || '';
            return json;
        }
        export_for_printing() {
            const result = super.export_for_printing(...arguments);
            result.bluemax_data = this.bluemax_data || false;
            result.transaction_id = this.transaction_id || '';
            result.entrymode = this.entrymode || '';
            result.card_type = this.card_type || '';
            result.card_number = this.card_number;
            result.response_message = this.bluemaxpay_response || '';
            result.approved_amount = this.approved_amount || 0.00;
            result.ref_number = this.ref_number || '';
            result.auth_code = this.auth_code || '';
            return result;
        }
    }
    Registries.Model.extend(Payment, PosBluemaxPaymentLine);
});