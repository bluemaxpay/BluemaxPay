odoo.define('pos_card_not_present.models', function(require) {

    var models = require('point_of_sale.models');
    var PaymentBlueMaxPayPay = require('pos_card_not_present.payment');
    models.register_payment_method('card_not_present', PaymentBlueMaxPayPay)
});