/** @odoo-module **/

import { _t } from '@web/core/l10n/translation';
import { Component } from '@odoo/owl';

import PaymentForm from '@payment/js/payment_form';

PaymentForm.include({
    events: Object.assign({}, PaymentForm.prototype.events || {}, {
        'change input[name="knk_donation_amount"]': '_updateAmount',
        'click .custom-radio': '_onClickCustomRadio',
        'click .custom-radio input[type="radio"]': '_onHiddenRadioClick',
        'input .o_amount_input': '_onOtherAmountInput',
        'change select[name="country_id"]': '_onChangeDonationCountry',
    }),

    // #=== WIDGET LIFECYCLE ===#

    /**
     * @override
     */
    async start() {
        Component.env.bus.addEventListener('update_shipping_cost', (ev) => this._updateShippingCost(ev.detail));
        return await this._super.apply(this, arguments);
    },

    _onClickCustomRadio: function (ev) {
        var $target = $(ev.currentTarget);
        var $amountInput = $target.closest('.knk_donation_payment_form').find('.o_amount_input');
        // Clear the value of the input field
        $amountInput.val('');
        $target.closest('.knk_donation_payment_form').find('#other_amount').prop('checked', false);
        $target.siblings().removeClass('active');
        $target.addClass('active');
        $target.find('input[type="radio"]').click();
    },

    _onHiddenRadioClick: function (ev) {
        // Stop propagation to prevent double triggering
        ev.stopPropagation();
    },

    _onOtherAmountInput: function (ev) {
        var $target = $(ev.currentTarget);
        var $radio = $target.closest('.knk_donation_payment_form').find('.custom-radio-container').find('input[type="radio"]');
        // Uncheck the radio button and remove active class when input is not empty
        if ($target.val().trim() !== '') {
            $radio.prop('checked', false);
            $target.closest('.knk_donation_payment_form').find('.custom-radio-container').find('.custom-radio').removeClass('active');
        }
    },

    _onChangeDonationCountry: function () {
        if (!$("#country_id").val()) {
            return;
        }
        return this.rpc("/donation/country_infos/" + $("#country_id").val(), {
        }).then(function (data) {
            // placeholder phone_code
            $("input[name='phone']").attr('placeholder', data.phone_code !== 0 ? '+'+ data.phone_code : '');

            // populate states and display
            var selectStates = $("select[name='state_id']");
            // dont reload state at first loading (done in qweb)
            if (selectStates.data('init')===0 || selectStates.find('option').length===1) {
                if (data.states.length || data.state_required) {
                    selectStates.html('');
                    data.states.forEach((x) => {
                        var opt = $('<option>').text(x[1])
                            .attr('value', x[0])
                            .attr('data-code', x[2]);
                        selectStates.append(opt);
                    });
                    selectStates.parent('div').show();
                } else {
                    selectStates.val('').parent('div').hide();
                }
                selectStates.data('init', 0);
            } else {
                selectStates.data('init', 0);
            }
        });
    },

    // #=== EVENT HANDLERS ===#

    /**
     * Update the amount in the payment context with the user input.
     *
     * @private
     * @param {Event} ev
     * @return {void}
     */
    _updateAmount(ev) {
        if (ev.target.value > 0) {
            this.paymentContext.amount = ev.target.value;
        }
    },


    /**
     * Update the total amount to be paid.
     *
     * Called upon change of shipping method
     *
     * @private
     * @param {float} amount
     */
     _updateShippingCost: function (amount) {
        this.paymentContext.amount = amount;
     },

    // #=== PAYMENT FLOW ===#

    /**
     * Perform some validations for donations before processing the payment flow.
     *
     * @override method from @payment/js/payment_form
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The payment flow of the selected payment option.
     * @return {void}
     */
    async _initiatePaymentFlow(providerCode, paymentOptionId, paymentMethodCode, flow) {
        if ($('.knk_donation_payment_form').length) {
            const errorFields = {};
            if (!this.$('input[name="email"]')[0].checkValidity()) {
                errorFields['email'] = _t("Email is invalid");
            }
            const mandatoryFields = {
                'name': _t('Name'),
                'email': _t('Email'),
                'country_id': _t('Country'),
            };
            for (const id in mandatoryFields) {
                const $field = this.$('input[name="' + id + '"],select[name="' + id + '"]');
                $field.removeClass('is-invalid').popover('dispose');
                if (!$field.val().trim()) {
                    errorFields[id] = _t("Field '%s' is mandatory", mandatoryFields[id]);
                }
            }
            if (Object.keys(errorFields).length) {
                for (const id in errorFields) {
                    const $field = this.$('input[name="' + id + '"],select[name="' + id + '"]');
                    $field.addClass('is-invalid');
                    $field.popover({content: errorFields[id], trigger: 'hover', container: 'body', placement: 'top'});
                }
                this._displayErrorDialog(
                    _t("Payment processing failed"),
                    _t("Some information is missing to process your payment.")
                );
                return;
            }
        }
        await this._super(...arguments);
    },

    /**
     * Add params used by the donation snippet for the RPC to the transaction route.
     *
     * @override method from @payment/js/payment_form
     * @private
     * @return {object} The extended transaction route params.
     */
    _prepareTransactionRouteParams() {
        const transactionRouteParams = this._super(...arguments);
        return $('.knk_donation_payment_form').length ? {
            ...transactionRouteParams,
            'partner_id': parseInt(this.paymentContext['partnerId']),
            'currency_id': this.paymentContext['currencyId']
                    ? parseInt(this.paymentContext['currencyId']) : null,
            'reference_prefix':this.paymentContext['referencePrefix']?.toString(),
            'partner_details': {
                'name': this.$('input[name="name"]').val(),
                'street': this.$('input[name="street"]').val(),
                'email': this.$('input[name="email"]').val(),
                'phone': this.$('input[name="phone"]').val(),
                'city': this.$('input[name="city"]').val(),
                'zip': this.$('input[name="zip"]').val(),
                'country_id': this.$('select[name="country_id"]').val(),
                'state_id': this.$('select[name="state_id"]').val(),
            },
            'donation_comment': this.$('#donation_comment').val(),
            'donation_recipient_email': this.$('input[name="donation_recipient_email"]').val(),
        } : transactionRouteParams;
    },

});
