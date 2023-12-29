/** @odoo-module **/


import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { SavedCardsPopup } from "@pos_card_not_present/js/saved_cards_popup";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

export class SavedCards extends PaymentInterface {
    setup() {
        super.setup(...arguments);
    }

    async send_payment_request(cid) {
        console.log('******latest one******')
        var PaymentLine = this.pos.get_order().selected_paymentline
        var PaymentTerminal = PaymentLine.payment_method.use_payment_terminal
        this._reset_state();
        if (PaymentLine.amount <= 0) {
            this._show_error(_t('Cannot process transactions with negative amount.'));
            if (PaymentTerminal == 'savedcards') {}
        } else if (PaymentTerminal == 'savedcards') {
            console.log('**************', this)
            if (!this.payment_method.developer_id || !this.payment_method.version_number || !this.payment_method.secret_api_key || !this.payment_method.public_api_key) {
                this._show_error(_t('Please Add API credentials on selection Payment Method'));
            }

            const { confirmed } = this.env.services.popup.add(SavedCardsPopup, {
                title: _t('BlueMax Pay Payment'),
                confirmText: _t("Payment"),
                cancelText: _t("Cancel"),
                payment_method: this.payment_method.id,
                parent: this,
                token: this.pos.bluemaxpay,
                name: this.pos.name,
                order: this.pos.get_order(),
                number: this.pos.number,
                year: this.pos.year,
                month: this.pos.month,
                cvv: this.pos.cvv,
            });
            if (confirmed) {
                const order = this.pos.get_order();
            }
        }
    }
    async send_payment_cancel(order, cid) {
        order.selected_paymentline.set_payment_status('retry');
        return Promise.resolve();
        this._super.apply(this, arguments);
    }
    async send_payment_reversal(cid) {
        this._super.apply(this, arguments);
        this.pos.get_order().selected_paymentline.set_payment_status('reversing');
        return this._sendTransaction(timapi.constants.TransactionType.reversal);
    }

    async close() {
        this._super.apply(this, arguments);
    }

    set_most_recent_service_id(id) {
        this.most_recent_service_id = id;
    }

    pending_bluemaxpay_line() {
        return this.pos.get_order().paymentlines.find(
            paymentLine => paymentLine.payment_method.use_payment_terminal === 'savedcards' && (!paymentLine.is_done()));
    }

    // private methods
    _reset_state() {
        this.was_cancelled = false;
        this.last_diagnosis_service_id = false;
        this.remaining_polls = 4;
        clearTimeout(this.polling);
    }

    _handle_odoo_connection_failure(data) {
        // handle timeout
        var line = this.pending_bluemaxpay_line();
        if (line) {
            line.set_payment_status('retry');
        }
        this._show_error(_t('Could not connect to the Odoo server, please check your internet connection and try again.'));

        return Promise.reject(data);
    }

    _convert_receipt_info(output_text) {
        return output_text.reduce(function(acc, entry) {
            var params = new URLSearchParams(entry.Text);

            if (params.get('name') && !params.get('value')) {
                return acc + _.str.sprintf('<br/>%s', params.get('name'));
            } else if (params.get('name') && params.get('value')) {
                return acc + _.str.sprintf('<br/>%s: %s', params.get('name'), params.get('value'));
            }

            return acc;
        }, '');
    }

    _show_error(msg, title) {
        if (!title) {
            title = _t('BlueMax Pay Error');
        }
        this.env.services.popup.add(ErrorPopup, {
            'title': title,
            'body': msg,
        });
    }
};
SavedCards.template = 'SavedCards';