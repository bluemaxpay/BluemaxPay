/* global waitForWebfonts */
odoo.define('pos_customer_screen.pos', function (require) {
"use strict";
const { PosGlobalState, Order, Orderline, Payment } = require('point_of_sale.models');
const { uuidv4 } = require("point_of_sale.utils");
const PosComponent = require('point_of_sale.PosComponent');
const ProductScreen = require('point_of_sale.ProductScreen');
const { useListener } = require("@web/core/utils/hooks");
const Registries = require('point_of_sale.Registries');

const PosCustomGlobalState = (PosGlobalState) => class PosCustomGlobalState extends PosGlobalState {
    constructor(obj) {
        super(obj);
        const storedCurrentsession_id = sessionStorage.getItem('current_session_id');
        if(!storedCurrentsession_id){
            const cstid = uuidv4();
            sessionStorage.setItem('current_session_id', cstid);
        }
    }
    send_current_order_to_customer_facing_display() {
        var self = this;
        if (!this.config.iface_customer_facing_display) return;
        this.render_html_for_customer_facing_display().then((rendered_html) => {
            if(this.env.pos.config.customer_screen_user_id){
                self.update_bus_channer(rendered_html);
            }else{
                if (self.env.pos.customer_display) {
                    var $renderedHtml = $('<div>').html(rendered_html);
                    $(self.env.pos.customer_display.document.body).html($renderedHtml.find('.pos-customer_facing_display'));
                    var orderlines = $(self.env.pos.customer_display.document.body).find('.pos_orderlines_list');
                    orderlines.scrollTop(orderlines.prop("scrollHeight"));
                } else if (this.config.iface_customer_facing_display_via_proxy && this.env.proxy.posbox_supports_display) {
                    this.env.proxy.update_customer_facing_display(rendered_html);
                }
            }
        });
    }
    update_bus_channer(rendered_html){
        var vals = {'current_session_id': sessionStorage.getItem('current_session_id'), 'datas': rendered_html};
        if(this.env.pos.config.customer_screen_user_id){
            this.env.services.rpc({
                model: 'bus.bus',
                method: 'sendposdata',
                args: [this.env.pos.config.customer_screen_user_id[0], vals],
            },{
                timeout: 5000,
                shadow: true,
            });
        }
        
    }
}
Registries.Model.extend(PosGlobalState, PosCustomGlobalState);

    class CustomerScreenButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick() {
            //var url = window.location.origin +'/web/login?redirect='+ '/pos_screen_datas/'+sessionStorage.getItem('current_session_id') +'&debug=assets';
            var url = '/pos_screen_datas/'+sessionStorage.getItem('current_session_id');
            window.location.href = `intent://customerscreen?url=${this.env.pos.base_url}/web/login?redirect=${url}#Intent;scheme=customerscreen;package=com.android.rockchip.dualscreendemo;end;`;
        }
    }
    CustomerScreenButton.template = 'CustomerScreenButton';

    ProductScreen.addControlButton({
        component: CustomerScreenButton,
        condition: function() {
            return this.env.pos.config.customer_screen_user_id;
        },
    });

    Registries.Component.add(CustomerScreenButton);
});