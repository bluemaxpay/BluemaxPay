/** @odoo-module **/


import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { PAX } from "@pos_card_present/js/pax";

export class PaymentCardPresent extends PaymentInterface {

    async send_payment_request(cid) {

        var self = this;
        var PaymentLine = this.pos.get_order().selected_paymentline
        var PaymentTerminal = PaymentLine.payment_method.use_payment_terminal
        // debugger;
        await super.send_payment_request(...arguments);
        var order = this.pos.get_order()
        this._reset_state();
        if (PaymentLine.amount <= 0) {
            if (!PaymentLine.transaction_id) {
                this._show_error('You cannot refund this Transaction, it does not contain bluemaxpay transaction ID', "Connection Error");
                order.stop_electronic_payment();
            }
            if (PaymentTerminal == 'card_present' && PaymentLine.transaction_id) {
                this.env.services.orm.silent.call(
                    'pos.payment.method',
                    'get_payment_method_details',
                    [this.payment_method.id]
                ).then(function(result) {
                    console.log(result, 'resss')
                    self.ip = (result.ip == '') ? '127.0.0.1' : result.ip;
                    self.port = (result.port == '') ? 10009 : result.port;
                    self.timeout = (result.timeout == '') ? 120 : result.timeout;
                    self.version = (result.version == '') ? 1.28 : result.version;
                    console.log(self.port, self.ip, 'portttt')
                    var HostSettings = self.host_settings(self.ip, self.port);
                    if (HostSettings) {
                        console.log(true);
                    } else {
                        console.log(false);
                    }
                    PAX.mDestinationIP = self.ip + ':' + self.port;
                    var TimeoutSetting = self.TimeoutSetting(self.timeout);
                    var DoCredit = self.DoCredit();
                })
            }
        } else if (PaymentTerminal == 'card_present') {
            this.env.services.orm.silent.call(
                'pos.payment.method',
                'get_payment_method_details',
                [this.payment_method.id]
            ).then(function(result) {
                console.log(result, 'resss')
                self.ip = (result.ip == '') ? '127.0.0.1' : result.ip;
                self.port = (result.port == '') ? 10009 : result.port;
                self.timeout = (result.timeout == '') ? 120 : result.timeout;
                self.version = (result.version == '') ? 1.28 : result.version;
                console.log(self.port, self.ip, 'port')
                var HostSettings = self.host_settings(self.ip, self.port);
                if (HostSettings) {
                    console.log(true);
                } else {
                    console.log(false);
                }
                PAX.mDestinationIP = self.ip + ':' + self.port;
                var TimeoutSetting = self.TimeoutSetting(self.timeout);
                var DoCredit = self.DoCredit(self.version);
            });
        }
    }

    Initialize(ip, port, version) {
        PAX.Initialize({
            "command": 'A00',
            "version": version
        }, function(response) {
            console.log(response, 'Initialize')
            return response
        })
    }
    TimeoutSetting(timeout) {
        timeout = (timeout * 1000).toString();
        PAX.AjaxTimeOut("Initialize", timeout);
        PAX.AjaxTimeOut("GetSignature", timeout);
        PAX.AjaxTimeOut("DoSignature", timeout);
        PAX.AjaxTimeOut("DoCredit", timeout);
    }
    DoCredit(version) {
        var self = this;
        self.Initialize(self.ip, self.port, version);
        var type = '01';
        var amount = 0;
        var tip = 0;
        var cashback = 0;
        var fee = 0;
        var tax = 0;
        var fual = 0;
        var ResponseCode = ''
        var ResponseMessage = ''
        var order = this.pos.get_order();
        console.log("order>>>>>>>>>>", order);
        amount = parseFloat(order.selected_paymentline.amount).toFixed(2);
        if (amount < 0) {
            amount = parseFloat(amount *= -1).toFixed(2);
            type = '02';
        }
        var amountInformation = {};
        var accountInformation = {};
        var traceInformation = {};
        var avsInformation = {};
        var cashierInformation = {};
        var commercialInformation = {};
        var motoEcommerce = {};
        var additionalInformation = {};
        amountInformation.TransactionAmount = parseInt(amount * 100);
        amountInformation.TipAmount = parseInt(tip * 100);
        amountInformation.CashBackAmount = parseInt(cashback * 100);
        amountInformation.MerchantFee = parseInt(fee * 100);
        amountInformation.TaxAmount = parseInt(tax * 100);
        amountInformation.FuelAmount = parseInt(fual * 100);
        console.log(amountInformation);
        traceInformation.ReferenceNumber = order.uid;
        console.log(amountInformation);
        var PaymentScreen = document.getElementsByClassName('pos-content')
        console.log(order.selected_paymentline, 'order')
        order.selected_paymentline.set_payment_status('waitingCard');
        var docredit = PAX.DoCredit({
            "command": 'T00',
            "version": version,
            "transactionType": type,
            "amountInformation": amountInformation,
            "accountInformation": accountInformation,
            "traceInformation": traceInformation,
            "avsInformation": avsInformation,
            "cashierInformation": cashierInformation,
            "commercialInformation": commercialInformation,
            "motoEcommerce": motoEcommerce,
            "additionalInformation": additionalInformation
        }, function(response) {
            console.log(response, 'DoCredit')
            console.log(order.selected_paymentline)
            ResponseCode = response[4]
            ResponseMessage = response[5]
            order.selected_paymentline.set_payment_status('retry');
            if (ResponseCode == '000000') {
                // debugger;
                console.log('**** response', response)
                console.log('**** response', response[10])
                order.selected_paymentline.amount = response[8][0] / 100
                order.selected_paymentline.transaction_id = response[14][2].split('=')[1]
                order.selected_paymentline.approved_amount = response[8][0] / 100
                order.selected_paymentline.bluemaxpay_response = response[6][1]
                order.selected_paymentline.ref_number = response[6][3]
                order.selected_paymentline.card_type = response[14][13].split('=')[1]
                order.selected_paymentline.card_number = '****' + response[9][0]
                order.selected_paymentline.auth_code = response[6][2]
                order.selected_paymentline.avs_resp = response[11][1]
                order.selected_paymentline.href = response[14][2].split('=')[1]
                order.selected_paymentline.device_id = ''
                order.selected_paymentline.transaction = response[10][0]
                order.selected_paymentline.set_payment_status('done');
            }
            if (ResponseCode != '000000') {
                posmodel.env.services.popup.add(ErrorPopup, {
                    'title': ("BlueMax Pay Error"),
                    'body': (ResponseMessage)
                });
            }
        })
        console.log(docredit, 'dooooooooooooooo')
    }
    host_settings(ip, port) {
        var reg = /^(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|0\d\d|1\d\d|2[0-4]\d|25[0-5])$/
        console.log(reg.test(ip), 'reg');
        var ipArr = ip.split(".");
        for (var i = 0; i < ipArr.length; i++) {
            if (ipArr[i].length > 1 && ipArr[i][0] == '0') {
                ipArr[i] = ipArr[i].substring(1);
            }
        }
        ip = ipArr.join(".");
        PAX.Settings(ip, port);
        return reg.test(ip)
    }
    send_payment_cancel(order, cid) {
        super.send_payment_cancel(...arguments);
        // this._super.apply(this, arguments);
        let line = this.pos.get_order().selected_paymentline
        line.set_payment_status('retry');
        return true;
    }
    send_payment_reversal(cid) {
        super.send_payment_reversal(...arguments);

        // this._super.apply(this, arguments);
        this.pos.get_order().selected_paymentline.set_payment_status('reversing');
        return this._sendTransaction(timapi.constants.TransactionType.reversal);
    }
    close() {
        super.close(...arguments);

        // this._super.apply(this, arguments);
    }
    set_most_recent_service_id(id) {
        this.most_recent_service_id = id;
    }
    pending_bluemaxpay_line() {
        return this.pos.get_order().paymentlines.find(
            paymentLine => paymentLine.payment_method.use_payment_terminal === 'card_present' && (!paymentLine.is_done()));
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
        posmodel.env.services.popup.add(ErrorPopup, {
            'title': title,
            'body': msg,
        });
    }
};