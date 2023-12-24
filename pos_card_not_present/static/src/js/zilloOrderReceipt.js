odoo.define('pos_card_not_present.receipt', function(require) {
    "use strict";
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    var ajax = require("web.ajax");

    const OrderReceiptTran = (OrderReceipt) =>
        class extends OrderReceipt {
            get isEnable() {
                self = this
                if (this.env.pos) {
                    if (self.line.payment_method.enable_card_details) {
                        return true
                    } else {
                        return false
                    }
                }
                return false
            }
        };
    Registries.Component.extend(OrderReceipt, OrderReceiptTran);
    return OrderReceipt;
});