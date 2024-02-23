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
import { sprintf } from "@web/core/utils/strings";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";


class ProcessPaymentWidget extends Component {
    static template = "web.AttachDocument";
    static props = {
        ...standardWidgetProps,
        string: { type: String },
    	action: { type: String, optional: true },
    	// highlight: { type: Boolean },
    	terminal_id: { type: String, optional: true },
    	terminal_name: { type: String, optional: true },
    	amount_pax: { type: String, optional: true }
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
        this.Customprops = this.props;
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
        var terminal_id = parseInt(this.props.record.data.id);
        // framework.blockUI();
        //            this.state.data.response_message = 'abcddd'
        //            console.log('this.state.data', this.state.data)
        var self = this;
        self.env.services.orm.silent.call(
            'account.payment.method',
            'get_device_details',
            [
                [],
                [terminal_id]
            ]
        ).then(function(result) {
            console.log('ooo', result)
            console.log(result.ip)

            if (!result.error) {
                self.HostSettings(result.ip, result.port)
                var credit = 'test'
                // framework.unblockUI();

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
        if (this.amount) {
            amount = this.amount.value
        } else {
            amount = this.props.record.data.amount_pax
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
        amountInformation.TransactionAmount = Math.round(amount * 100);
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
            var ResponseApproveMessage = ''
            var ResponseApproveAmt = 0.0
            if (ResponseMessage == 'OK')
            {
                ResponseApproveMessage =  response[6][1]
                ResponseApproveAmt = response[8][0] / 100
            }

            if (ResponseCode == '000000') {
                ResponseId = response[10][0]
                $('.btn-close').hide()
                $('.oe_background_greyssdfsdf').hide()
                $('.show_confirm_message').show()
                var terminal_id = parseInt(self.props.record.data.id);

                var context = self.props.record.context
                var active_id = context.active_id
                var active_model = context.active_model
                if (active_model == 'account.move.line')
                {
                    active_model = 'account.move'
                }
                console.log('000000', active_model, active_id)
                self.env.services.orm.silent.call(
                    active_model,
                    "get_response_message",
                    [active_id, ResponseCode, ResponseId, response, terminal_id, ResponseApproveAmt]
                ).then(function(result) {
                    console.log(result, 'res')
                    $('#create-bluemaxpay-payment').show()
                    $('.btn-close').hide()
                    self.props.record.model.dialog.add(ConfirmationDialog, {
                        body:sprintf(_t('Payment is completed. Response message: %s | %s. Amount: $%s'), ResponseMessage, ResponseApproveMessage, ResponseApproveAmt),
                    });
                    $('.btn-close').hide()

                });

            } else {
                console.log('!000000', active_model, active_id)
                var context = self.props.record.context
                var active_id = context.active_id
                var active_model = context.active_model
                var terminal_id = parseInt(self.props.record.data.id);
                if (active_model == 'account.move.line')
                {
                    active_model = 'account.move'
                }

                console.log(active_model, active_id)
                self.env.services.orm.silent.call(
                    active_model,
                    "get_response_message",
                    [active_id, ResponseCode, ResponseId, response, terminal_id, ResponseApproveAmt]
                ).then(function(result) {
                    $('#create-bluemaxpay-payment').show()
                    self.props.record.model.dialog.add(ConfirmationDialog, {
                        body:sprintf(_t('Payment is not completed. Response message: %s'), ResponseMessage),
                    });
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
        this.onClickBlueMaxPayCardPresentInvoice()
        //        if (await this.beforeOpen()) {
        //            this.fileInput.click();
        //        }
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
            terminal_name: attrs.terminal_name,
            terminal_name: attrs.terminal_name,
            terminal_id: attrs.terminal_id,
            action: attrs.action,
            string: attrs.string,
        };
    },
};


registry.category("view_widgets").add("payment_process", processPaymentWidget);
