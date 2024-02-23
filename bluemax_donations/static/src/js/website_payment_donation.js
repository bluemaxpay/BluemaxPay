/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';

publicWidget.registry.KnkWebsitePaymentDonation = publicWidget.Widget.extend({
    selector: '.knk_donation_payment_form',
    events: {
        'focus .o_amount_input': '_onFocusAmountInput',
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     * @param {Event} ev
     */
    _onFocusAmountInput(ev) {
        this.$el.find('#other_amount').prop("checked", true);
    },
});
