/** @odoo-module **/
import { FileInput } from "@web/core/file_input/file_input";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import rpc from 'web.rpc';
import { _t } from 'web.core';
import Dialog from 'web.Dialog';
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";
import pax from "invoice_card_present.pax";
const { Component, useState } = owl;
import framework from "web.framework";

class ProcessPaymentWidget extends Component {
    setup() {
        // debugger
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
    }

    async onInputChange() {
        // debugger;
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
        framework.blockUI();
        //            this.state.data.response_message = 'abcddd'
        //            console.log('this.state.data', this.state.data)
        var self = this;
        rpc.query({
            model: 'account.payment.method',
            method: 'get_device_details',
            args: [
                []
            ]
        }).then(function(result) {
            console.log('ooo', result)
            console.log(result.ip)
            if (!result.error) {
                self.HostSettings(result.ip, result.port)
                var credit = 'test'
                framework.unblockUI();


                credit = self.DoCredit('01')
                return Promise.resolve();

                return Promise.resolve();
            } else {
                // debugger;
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
            //                console.log(credit)

        });

    }

    //            const $checkedRadios = this.$('input[name="o_payment_radio"]:checked');
    //            if ($checkedRadios.length !== 1) { // Cannot find selected payment option, show dialog
    //                return new Dialog(null, {
    //                    title: _.str.sprintf(_t("Error: %s"), title),
    //                    size: 'medium',
    //                    $content: `<p>${_.str.escapeHTML(description) || ''}</p>`,
    //                    buttons: [{text: _t("Ok"), close: true}]
    //                }).open();
    //            } else { // Show error in inline form
    //                this._hideError(); // Remove any previous error
    //
    //                // Build the html for the error
    //                let errorHtml = `<div class="alert alert-danger mb4" name="o_payment_error">
    //                                 <b>${_.str.escapeHTML(title)}</b>`;
    //                if (description !== '') {
    //                    errorHtml += `</br>${_.str.escapeHTML(description)}`;
    //                }
    //                if (error !== '') {
    //                    errorHtml += `</br>${_.str.escapeHTML(error)}`;
    //                }
    //                errorHtml += '</div>';
    //
    //                // Append error to inline form and center the page on the error
    //                const checkedRadio = $checkedRadios[0];
    //                const paymentOptionId = this._getPaymentOptionIdFromRadio(checkedRadio);
    //                const formType = $(checkedRadio).data('payment-option-type');
    //                const $inlineForm = this.$(`#o_payment_${formType}_inline_form_${paymentOptionId}`);
    //                $inlineForm.removeClass('d-none'); // Show the inline form even if it was empty
    //                $inlineForm.append(errorHtml).find('div[name="o_payment_error"]')[0]
    //                    .scrollIntoView({behavior: 'smooth', block: 'center'});
    //            }
    //            this._enableButton(); // Enable button back after it was disabled before processing
    //            $('body').unblock(); // The page is blocked at this point, unblock it

    async DoCredit(type) {
        var self = this;
        //            console.log('this', this.state)

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


        //            amount = parseFloat(order.selected_paymentline.amount).toFixed(2);
        // debugger;

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

        //            traceInformation.ReferenceNumber = order.uid;
        traceInformation.ReferenceNumber = 'this.state.date'
        console.log(amountInformation);
        //            var PaymentScreen = document.getElementsByClassName('pos-content')
        //            console.log(order.selected_paymentline, 'order')
        //            order.selected_paymentline.set_payment_status('waitingCard');

        //            var ConfirmPopup = Gui.showPopup('ConfirmPopup', {
        //                title: ("BlueMax Pay Confirm"),
        //                body: "Please swipe your card",
        //            });
        //            console.log(ConfirmPopup, 'Poooooopup')
        //            if (ConfirmPopup){
        //            console.log('aaaaaaaaaaa');
        //                ConfirmPopup.trigger('close-popup')
        //            }
        //            console.log($('PaymentScreen'))
        //            console.log('hhhhhhhhhhhhhh',$('.payment-buttons-container'))
        //            PaymentScreen.style.pointer-events = "none"
        //            var loader = document.getElementById('loader-bluemaxpay')
        //            loader.style.display = "block";

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
                self._rpc({
                    model: active_model,
                    method: "get_response_message",
                    args: [active_id, ResponseCode, ResponseId]
                }).then(function(result) {
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
                self._rpc({
                    model: active_model,
                    method: "get_response_message",
                    args: [active_id, ResponseCode, ResponseId]
                }).then(function(result) {
                    $('#create-bluemaxpay-payment').show()
                    Dialog.confirm(
                        this,
                        _.str.sprintf(_t('Payment is not completed. Response message: %s'), ResponseMessage), {}
                    );
                });
            }
        })
        if (ResponseCode == '') {
            //                order.selected_paymentline.set_payment_status('retry');
            //                Gui.showPopup("ErrorPopup", {
            //                    'title': ("BlueMax Pay Error"),
            //                    'body':  ('Connection Error')
            //                });
        }
    }
    async HostSettings(ip, port) {
        console.log(ip, port)
        pax.Settings(ip, port);
    }
    async Initialize() {
        console.log('tetytyg')
    }

    async triggerUpload() {
        // debugger;
        this.onClickBlueMaxPayCardPresentInvoice()
        //        if (await this.beforeOpen()) {
        //            this.fileInput.click();
        //        }
    }

    async onFileUploaded(files) {
        // debugger;
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
        // debugger;
        return this.props.record.save();
    }

}

ProcessPaymentWidget.template = "web.AttachDocument";
ProcessPaymentWidget.components = {
    FileInput,
};
ProcessPaymentWidget.props = {
    ...standardWidgetProps,
    string: { type: String },
    action: { type: String, optional: true },
    highlight: { type: Boolean },
};
ProcessPaymentWidget.extractProps = ({ attrs }) => {
    const { action, highlight, string } = attrs;
    return {
        action,
        highlight: !!highlight,
        string,
    };
};

registry.category("view_widgets").add("payment_process", ProcessPaymentWidget);