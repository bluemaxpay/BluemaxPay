/** @odoo-module **/

import { ReprintReceiptButton } from "@point_of_sale/app/screens/ticket_screen/reprint_receipt_button/reprint_receipt_button";
import { patch } from "@web/core/utils/patch";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";


patch(ReprintReceiptButton.prototype, {

    async click() {
        if (!this.props.order) return;
        const paymentDataArray = this.pos.pos_payment_data;
        const paymentLine = this.props.order.paymentlines[0];
        for (const paymentData of paymentDataArray) {
            if (paymentData.transaction_id === paymentLine.transaction_id) {
                if (paymentData.card_type) paymentLine.card_type = paymentData.card_type;
                if (paymentData.card_number) {
                    paymentLine.card_number = paymentData.card_number;
                } else {
                    paymentLine.card_number = '******';
                }
                if (paymentLine.payment_method.use_payment_terminal == 'bluemax') paymentLine.bluemax_data = true;
                if (paymentData.bluemaxpay_response) paymentLine.bluemaxpay_response = paymentData.bluemaxpay_response;
                if (paymentData.approved_amount) paymentLine.approved_amount = paymentData.approved_amount;
                if (paymentData.ref_number) paymentLine.ref_number = paymentData.ref_number;
                if (paymentData.auth_code) paymentLine.auth_code = paymentData.auth_code;
                if (paymentData.cardholder_name) paymentLine.cardholder_name = paymentData.cardholder_name;
                if (paymentData.avs_resp) paymentLine.avs_resp = paymentData.avs_resp;
                if (paymentData.device_id) paymentLine.device_id = paymentData.device_id;
                if (paymentData.href) paymentLine.href = paymentData.href;
                if (paymentData.transaction) paymentLine.transaction = paymentData.transaction;
                break;
            }
        }
        (await this.printer.print(OrderReceipt, {
            data: this.props.order.export_for_printing(),
            formatCurrency: this.env.utils.formatCurrency,
        })) || this.pos.showScreen("ReprintReceiptScreen", { order: this.props.order });
    }
});