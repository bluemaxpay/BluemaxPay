odoo.define('pos_card_present.models', function (require) {

    var models = require('point_of_sale.models');
    var PaymentCardPresent = require('pos_card_present.payment');
    models.register_payment_method('card_present', PaymentCardPresent);

});
