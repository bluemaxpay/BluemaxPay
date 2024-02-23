odoo.define('payment_bluemaxpay.ClientAction', function(require) {
    'use strict';

    var concurrency = require('web.concurrency');
    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var Dialog = require('web.Dialog');
    var field_utils = require('web.field_utils');
    var session = require('web.session');
    const { download } = require("@web/core/network/download");


    var QWeb = core.qweb;
    var _t = core._t;

    var ClientAction = AbstractAction.extend({
        contentTemplate: 'global_report',
        hasControlPanel: true,
        loadControlPanel: true,

        events: {
            'click .o_report_record_url': '_onClickRecordLink',
            'click .o_group_by_month': '_onClickGroupByMonth',
            'click .o_group_by_week': '_onClickGroupByWeek',
            'click .o_group_by_day': '_onClickGroupByDay',
            'click .o_group_by_year': '_onClickGroupByYear',
            'click .o_download_report': '_onClickExportReport'
        },

        init: function(parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
            this.context = action.context;
            this.companyId = false;
            this.formatFloat = field_utils.format.float;
            this.bmPeriods = [];
            this.bluemaxpay_transactions = false;
            this.active_ids = [];
            this.mutex = new concurrency.Mutex();
            this.searchModelConfig.modelName = 'global.bluemaxpay.report';
            this.domain = [];
        },


        willStart: function() {
            var self = this;
            var _super = this._super.bind(this);
            var args = arguments;
            var def_control_panel = this._rpc({
                    model: 'ir.model.data',
                    method: 'check_object_reference',
                    args: ['payment_bluemaxpay', 'global_bluemaxpay_report_search_view'],
                    kwargs: { context: session.user_context },
                })
                .then(function(viewId) {
                    self.viewId = viewId[1];
                });

            var def_content = this._getRecordIds();
            return Promise.all([def_content, def_control_panel]).then(function() {
                return self._get_bluemaxpay_transactions().then(function() {
                    return _super.apply(self, args);
                });
            });
        },

        start: async function() {
            this.$buttons = $(
                QWeb.render(
                    "payment_bluemaxpay.client_action.ControlButtons", {}
                )
            );


            this.controlPanelProps.cp_content = {
                $buttons: this.$buttons,
            };
            await this._super(...arguments);
            if (this.bluemaxpay_transactions.length == 0) {
                this.$el.find('.o_report').append($(QWeb.render('bm_report_nocontent_helper')));
            }
            this._controlPanelWrapper.update(this.controlPanelProps);
        },

        _showDatePickerPopup: function() {
            var self = this;
            var dialog = new Dialog(this, {
                title: _t('Select Date Range For Export'),
                size: 'small',
                $content: $(QWeb.render("payment_bluemaxpay.client_action.DatePickerPopup")),
                buttons: [{
                    text: _t("Export"),
                    classes: 'btn-primary',
                    click: function() {
                        var startDate = dialog.$(".start-date").val();
                        var endDate = dialog.$(".end-date").val();
                        if (!startDate || !endDate) {
                            return;
                        }
                        dialog.close();
                        self._onClickDownloadReport(startDate, endDate);
                    }
                }, {
                    text: _t("Cancel"),
                    close: true
                }]
            });
            dialog.open();
        },

        _onClickExportReport: function(ev) {
            ev.preventDefault();
            this._showDatePickerPopup();
        },

        _onClickDownloadReport: function(startDate, endDate) {
            var table = []
            var table_headers = $('table.bm_table').find('thead.bm_report_header');
            var table_bodies = $('table.bm_table').find('tbody.bm_report_content');
            var filtered_data = [];

            _.each(table_headers.find('tr'), function(tr) {
                var header_data = _.map($(tr).find('th'), (x) => $(x).attr('value') ? $(x).attr('value') : '');
                table.push(header_data);
            })
            var exportable_tr = _.filter($(table_bodies).find('tr'), (tr) => !$(tr).hasClass('d-none'));
            _.each(exportable_tr, function(tr) {
                var body_data = _.map($(tr).find('th'), (x) => $(x).attr('value'));
                table.push(body_data);
            })

            download({
                url: "/bmpay/report/export_xlsx",
                data: { data: JSON.stringify(table), startDate: startDate, endDate: endDate },
            });
        },

        _getRecordIds: function() {
            var self = this;
            return this._rpc({
                model: 'global.bluemaxpay.report',
                method: 'search_read',
                domain: this.domain,
                fields: ['transaction_id'],
            }).then(function(ids) {
                self.active_ids = ids;
            });
        },

        _reloadContent: function() {
            var self = this;
            return this._get_bluemaxpay_transactions()

        },

        _get_bluemaxpay_transactions: function() {
            var self = this;
            var domain = this.domain;
            return this._rpc({
                model: 'global.bluemaxpay.report',
                method: 'get_bluemaxpay_transactions',
                args: [domain],
            }).then(function(transactions) {

                self.bluemaxpay_transactions = transactions.bluemaxpay_transactions;
                return transactions.bluemaxpay_transactions;
            });
        },



        _onClickGroupByMonth: function(ev) {
            ev.preventDefault();
            this._get_bluemaxpay_transactions('month');
        },

        _onClickGroupByWeek: function(ev) {
            ev.preventDefault();
            this._get_bluemaxpay_transactions('week');
        },

        _onClickGroupByDay: function(ev) {
            ev.preventDefault();
            this._get_bluemaxpay_transactions('day');
        },

        _onClickGroupByYear: function(ev) {
            ev.preventDefault();
            this._get_bluemaxpay_transactions('year');
        },

        _onClickRecordLink: function(ev) {
            ev.preventDefault();
            return this.do_action({
                type: 'ir.actions.act_window',
                res_model: $(ev.currentTarget).data('model'),
                res_id: $(ev.currentTarget).data('res-id'),
                views: [
                    [false, 'form']
                ],
                target: 'current'
            });
        },

    });

    core.action_registry.add('global_bluemaxpay_report_client_action', ClientAction);

    return ClientAction;

});