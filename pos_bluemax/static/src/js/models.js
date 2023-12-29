/** @odoo-module */
import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentBluemax } from "@pos_bluemax/js/payment_bluemax";
import { Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

register_payment_method("bluemax", PaymentBluemax);

patch(Payment.prototype, {
    setup() {
        super.setup(...arguments);
        this.bluemax_data = this.bluemax_data || false;
        this.entrymode = this.entrymode || null;;
        this.card_type = this.card_type || null;;
        this.card_number = this.card_number || null;;
        this.bluemaxpay_response = this.bluemaxpay_response || null;;
        this.approved_amount = this.approved_amount || 0.00;
        this.ref_number = this.ref_number || null;;
        this.auth_code = this.auth_code || null;;
    },
    //@override
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (json) {
            json.bluemax_data = this.bluemax_data;
            json.entrymode = this.entrymode;
            json.card_type = this.card_type;
            json.card_number = this.card_number;
            json.bluemaxpay_response = this.bluemaxpay_response;
            json.approved_amount = this.approved_amount;
            json.ref_number = this.ref_number;
            json.auth_code = this.auth_code;
            return json;

        }
        return json;
    },
    //@override
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        this.bluemax_data = json.bluemax_data;
        this.entrymode = json.entrymode;
        this.card_type = json.card_type;
        this.card_number = json.card_number;
        this.bluemaxpay_response = json.bluemaxpay_response;
        this.approved_amount = json.approved_amount;
        this.ref_number = json.ref_number;
        this.auth_code = json.auth_code;
    },
    //@override
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.bluemax_data = this.bluemax_data;
        result.transaction_id = this.transaction_id;
        result.entrymode = this.entrymode;
        result.card_type = this.card_type;
        result.card_number = this.card_number;
        result.response_message = this.bluemaxpay_response;
        result.approved_amount = this.approved_amount;
        result.ref_number = this.ref_number;
        result.auth_code = this.auth_code;
        return result;
    },
});