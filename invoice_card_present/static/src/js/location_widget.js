/** @odoo-module **/
import { FileInput } from "@web/core/file_input/file_input";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import pax from "@invoice_card_present/js/pax";
import { useState } from "@odoo/owl";
import { Component } from "@odoo/owl";


class ProcessPaymentWidget extends Component {
    static template = "web.AttachDocument";
    static props = {
        ...standardWidgetProps,
        text: { type: String },
        title: { type: String, optional: true },
        bgClass: { type: String, optional: true },
        string: { type: String },
        action: { type: String, optional: true },
    };
    static defaultProps = {
        title: "",
        bgClass: "text-bg-success",
    };

    setup() {
        this.http = useService("http");
        this.notification = useService("notification");
        this.fileInput = document.createElement("input");
        this.fileInput.type = "file";
        this.fileInput.accept = "*";
        this.fileInput.multiple = true;
        this.fileInput.onchange = this.onInputChange.bind(this);
        this.state = useState({
            displayError: false,
            message: '',
            loading: false,
        });
        this.rpc = useService("rpc");
    }

    async onInputChange() {
        const fileData = await this.http.post(
            "/web/binary/upload_attachment", {
                csrf_token: odoo.csrf_token,
                ufile: [...this.fileInput.files],
                model: this.props.record.resModel,
                id: this.props.record.resId,
            },
            "text"
        );
        const parsedFileData = JSON.parse(fileData);
        if (parsedFileData.error) {
            throw new Error(parsedFileData.error);
        }
        await this.onFileUploaded(parsedFileData);
    }
    async onClickBlueMaxPayCardPresentInvoice() {
        $('#create-bluemaxpay-payment').hide()
        var self = this;
        this.env.services.orm.silent.call(
            'account.payment.method',
            'get_device_details',
            [
                []
            ]
        ).then(function(result) {
            console.log('ooo', result)
            console.log(result.ip)
            if (!result.error) {
                self.HostSettings(result.ip, result.port)
                var credit = 'test'
                credit = self.DoCredit('01')
                return Promise.resolve();

                return Promise.resolve();
            } else {
                self.state.message = result.error
                self.state.displayError = true;
                fdisplayErrorramework.unblockUI();
                displayError
                Dialog.alert(this, "Dialog Alert", {
                    displayErroronForceClose: function() {
                        console.log("Click Close");
                    },
                    confirm_callback: function() {
                        console.log("Click Ok");

                    }
                });
                return Promise.resolve();
                console.log(result.error)
            }
        });
    }
    async DoCredit(type) {
        var self = this;
        var amount = 0;
        var tip = 0;
        var cashback = 0;
        var fee = 0;
        var tax = 0;
        var fual = 0;
        var ResponseCode = ''
        var ResponseMessage = ''
        var ResponseId = ''
        var active_model = ''
        var active_id = ''

        if (this.amount) {

            amount = this.amount.value
        } else {

            amount = this.props.record.data.amount
        };

        if (amount < 0) {
            this._show_error(_t('Cannot process transactions with negative amount.'));
            return Promise.resolve();
        }
        var amountInformation = {};
        var accountInformation = {};
        var traceInformation = {};
        var avsInformation = {};
        var version = {};
        var cashierInformation = {};
        var commercialInformation = {};
        var motoEcommerce = {};
        var additionalInformation = {};
        var self = this;
        amountInformation.TransactionAmount = parseInt(amount * 100);
        amountInformation.TipAmount = parseInt(tip * 100);
        amountInformation.CashBackAmount = parseInt(cashback * 100);
        amountInformation.MerchantFee = parseInt(fee * 100);
        amountInformation.TaxAmount = parseInt(tax * 100);
        amountInformation.FuelAmount = parseInt(fual * 100);
        console.log(amountInformation);
        traceInformation.ReferenceNumber = 'this.state.date'
        console.log(amountInformation);
        var docredit = pax.DoCredit({
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
            $('#create-bluemaxpay-payment').show()
            ResponseCode = response[4]
            ResponseMessage = response[5]
            if (ResponseCode == '000000') {
                ResponseId = response[10][0]

                var context = self.state.context
                var active_id = context.active_id
                var active_model = context.active_model
                console.log('000000', active_model, active_id)
                this.env.services.orm.silent.call(
                    active_model,
                    "get_response_message",
                    [active_id, ResponseCode, ResponseId]
                ).then(function(result) {
                    console.log(result, 'res')
                    $('#create-bluemaxpay-payment').show()
                    Dialog.confirm(
                        this,
                        _.str.sprintf(_t('Payment is completed. Response message: %s'), ResponseMessage), {}
                    );
                });

            } else {
                console.log('!000000', active_model, active_id)
                var context = self.state.context
                var active_id = context.active_id
                var active_model = context.active_model
                console.log(active_model, active_id)
                this.env.services.orm.silent.call(
                    active_model,
                    "get_response_message",
                    [active_id, ResponseCode, ResponseId]
                ).then(function(result) {
                    $('#create-bluemaxpay-payment').show()
                    Dialog.confirm(
                        this,
                        _.str.sprintf(_t('Payment is not completed. Response message: %s'), ResponseMessage), {}
                    );
                });
            }
        })
        if (ResponseCode == '') {}
    }
    async HostSettings(ip, port) {
        console.log(ip, port)
        pax.Settings(ip, port);
    }
    async Initialize() {
        console.log('tetytyg')
    }

    async triggerUpload() {
        this.onClickBlueMaxPayCardPresentInvoice()
    }

    async onFileUploaded(files) {
        const { action, record } = this.props;
        if (action) {
            const { model, resId, resModel } = record;
            await this.env.services.orm.call(resModel, action, [resId], {
                attachment_ids: files.map((file) => file.id),
            });
            await record.load();
            model.notify();
        }
    }
    beforeOpen() {
        return this.props.record.save();
    }
}

ProcessPaymentWidget.components = {
    FileInput,
};

export const processPaymentWidget = {
    component: ProcessPaymentWidget,
    extractProps: ({ attrs }) => {
        return {
            text: attrs.title || attrs.text,
            title: attrs.tooltip,
            bgClass: attrs.bg_color,
            action: attrs.action,
            string: attrs.string,
        };
    },
};

registry.category("view_widgets").add("payment_process", processPaymentWidget);