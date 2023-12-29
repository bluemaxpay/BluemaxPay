/** @odoo-module **/

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    export_for_printing() {
        // debugger;
        return {
            ...super.export_for_printing(),
            isEnable: this.paymentlines.find(
                (paymentLine) => {
                    return (
                        this.pos &&
                        paymentLine.payment_method.enable_card_details &&
                        (paymentLine.payment_method.use_payment_terminal === 'card_not_present' ||
                            paymentLine.payment_method.use_payment_terminal === 'savedcards')
                    );
                }),
        };
    },

});