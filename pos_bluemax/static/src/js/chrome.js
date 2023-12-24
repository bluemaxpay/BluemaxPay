odoo.define('pos_bluemax.Chrome', function(require) {
    'use strict';

    const Chrome = require('point_of_sale.Chrome');
    const Registries = require('point_of_sale.Registries');
    const PosTableChrome = (Chrome) =>
        class extends Chrome {
            /**
             * @override
             */
            async start() {
                await super.start();
                this.env.services.bus_service.addChannel('bluemax.pos.payment.channel');
                this.env.services.bus_service.addEventListener('notification', this._onPaymentNotification.bind(this));
            }
            _onPaymentNotification({ detail: notifications }) {
                for (var notif of notifications) {
                    if (notif.type == 'bluemax.pos.payment.channel' && notif.payload['payment_response'] != undefined) {
                        let order = this.env.pos.get_order();
                        if (notif.payload['payment_response'].orderid == order.uid){
                            this.env.pos.get_order().selected_paymentline.payment_method.payment_terminal.bluemax_validate(notif.payload['payment_response']);
                        }
                        // var user_id = notif.payload;
                        // var n = new Noty({
                        //     theme: 'light',
                        //     text: notif.payload.payment_response.table_order_message,
                        //     timeout: false,
                        //     layout: 'topRight',
                        //     type: 'success',
                        //     closeWith: ['button'],
                        //     sounds: {
                        //         sources: ['/qrcode_table/static/lib/noty/lib/done-for-you.mp3'],
                        //         volume: 1,
                        //         conditions: ['docVisible']
                        //     },
                        // });
                        // n.show();
                    }
                }
            }
        };
    Registries.Component.extend(Chrome, PosTableChrome);
});