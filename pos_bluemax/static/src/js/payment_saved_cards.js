odoo.define('pos_bluemax.payment', function(require) {
    "use strict";

    var core = require('web.core');
    var rpc = require('web.rpc');
    var PaymentInterface = require('point_of_sale.PaymentInterface');
    const { Gui } = require('point_of_sale.Gui');
    const Registries = require('point_of_sale.Registries');
    var _t = core._t;
    var PaymentCardNotPresent = PaymentInterface.extend({

        send_payment_request: async function(cid) {
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
                const { confirmed } = Gui.showPopup('CardNotPresentBlueMaxPayPayment2', {
                    title: _t('BlueMax Pay Payment'),
                    confirmText: _t("Payment"),
                    cancelText: _t("Cancel"),
                    payment_method: this.payment_method.id,
                    parent: this,
                    token: this.pos.bluemaxpay,
                    name: this.pos.name,
                    number: this.pos.number,
                    year: this.pos.year,
                    month: this.pos.month,
                    cvv: this.pos.cvv,
                });
                if (confirmed) {
                    const order = this.env.pos.get_order();
                }
            }
        },
        send_payment_cancel: function(order, cid) {
            order.selected_paymentline.set_payment_status('retry');
            return Promise.resolve();
            this._super.apply(this, arguments);
        },
        send_payment_reversal: function(cid) {
            this._super.apply(this, arguments);
            this.pos.get_order().selected_paymentline.set_payment_status('reversing');
            return this._sendTransaction(timapi.constants.TransactionType.reversal);
        },

        close: function() {
            this._super.apply(this, arguments);
        },

        set_most_recent_service_id(id) {
            this.most_recent_service_id = id;
        },

        pending_bluemaxpay_line() {
            return this.pos.get_order().paymentlines.find(
                paymentLine => paymentLine.payment_method.use_payment_terminal === 'savedcards' && (!paymentLine.is_done()));
        },

        // private methods
        _reset_state: function() {
            this.was_cancelled = false;
            this.last_diagnosis_service_id = false;
            this.remaining_polls = 4;
            clearTimeout(this.polling);
        },

        _handle_odoo_connection_failure: function(data) {
            // handle timeout
            var line = this.pending_bluemaxpay_line();
            if (line) {
                line.set_payment_status('retry');
            }
            this._show_error(_t('Could not connect to the Odoo server, please check your internet connection and try again.'));

            return Promise.reject(data);
        },

        _convert_receipt_info: function(output_text) {
            return output_text.reduce(function(acc, entry) {
                var params = new URLSearchParams(entry.Text);

                if (params.get('name') && !params.get('value')) {
                    return acc + _.str.sprintf('<br/>%s', params.get('name'));
                } else if (params.get('name') && params.get('value')) {
                    return acc + _.str.sprintf('<br/>%s: %s', params.get('name'), params.get('value'));
                }

                return acc;
            }, '');
        },

        _show_error: function(msg, title) {
            if (!title) {
                title = _t('BlueMax Pay Error');
            }
            Gui.showPopup('ErrorPopup', {
                'title': title,
                'body': msg,
            });
        },
    });
    PaymentCardNotPresent.template = 'PaymentCardNotPresent';
    Registries.Component.add(PaymentCardNotPresent);
    return PaymentCardNotPresent;
});