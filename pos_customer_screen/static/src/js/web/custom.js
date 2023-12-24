odoo.define('pos_customer_screen.custom', function (require) {
'use strict';
    const publicWidget = require('web.public.widget');
    publicWidget.registry.PosScreenData = publicWidget.Widget.extend({
        selector: '#pos_screen_data',
        events: {
        },
        init: function () {
            this._super.apply(this, arguments);
        },
        start: function () {
            var def = this._super.apply(this, arguments);
            this.call('bus_service', 'addChannel', 'pos_screen_order_datas');
            this.call('bus_service', 'addEventListener', 'notification', this._onScreenNotification.bind(this));
            return def;
        },
        _onScreenNotification({ detail: notifications }) {
            for (var notif of notifications) {
                if(notif.type == 'pos_screen_order_datas'){
                    var datas = notif.payload.datas;
                    var csession_id = notif.payload.current_session_id;
                    if(csession_id == this.$el.data('csession_id')){
                        var $renderedHtml = $('<div>').html(datas);
                        if(this.$el.find('.pos-customer_facing_display').length){
                            this.$el.find('.pos-customer_facing_display').replaceWith($renderedHtml.find('.pos-customer_facing_display'));
                        }else{
                            this.$el.html(datas);
                        }
                        var orderlines = this.$el.find('.pos_orderlines_list');
                        orderlines.scrollTop(orderlines.prop("scrollHeight"));
                    }
                }
            }
        },
    });
});