/** @odoo-module */


import { concurrency } from "@web/core/utils/concurrency";
import { renderToString } from "@web/core/utils/render";
import { formatFloat } from "@web/core/utils/numbers";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { session } from '@web/session';
import { Component, onMounted, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { ExportDialog } from "./ExportDialog";
import { download } from "@web/core/network/download";

export class ClientAction extends Component {
    setup() {
        super.setup();
        this.companyId = false;
        this.formatFloat = formatFloat;
        this.state = useState({
            bluemaxpay_transactions: [],
            bmPeriods: [],
            sum: false,
            results_months: [],
            results_days: [],
            results_years: [],
            groupby: false

        })
        this.active_ids = [];
        this.flag_month = false;
        this.flag_day = false;
        this.flag_year = false;
        this.modelName = 'global.bluemaxpay.report';
        this.domain = [];
        this._reloadContent(null);
    }

    async start() {
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
    }

    _showDatePickerPopup() {

        this.env.services.dialog.add(ExportDialog, {
            onExportConfirm: () => {
                var startDate = $(".start-date").val();
                var endDate = $(".end-date").val();
                if (!startDate || !endDate) {
                    return;
                }
                this._onClickDownloadReport(startDate, endDate);
            },
            close: () => {
                document.body.click();
            }
        });
    }

    _onClickExportReport(ev) {
        ev.preventDefault();
        this._showDatePickerPopup();
    }

    _onClickDownloadReport(startDate, endDate) {
        var table = []
        var table_headers = $('table.bm_table').find('thead.bm_report_header');
        var table_bodies = $('table.bm_table').find('tbody.bm_report_content');
        var filtered_data = [];

        table_headers.find('tr').each(function(index, tr) {
            var header_data = Object.values($(tr).find('th').map((index, x) => $(x).attr('value') ? $(x).attr('value') : ''));
            header_data.pop();
            header_data.pop();
            table.push(header_data);
        })
        var exportable_tr = $(table_bodies).find('tr').filter();
        exportable_tr.prevObject.each(function(index, tr) {
            var body_data = Object.values($(tr).find('th').map((index, x) => $(x).attr('value') ? $(x).attr('value') : ''));
            body_data.pop();
            body_data.pop();
            table.push(body_data);
        })
        download({
            url: "/bmpay/report/export_xlsx",
            data: { data: JSON.stringify(table), startDate: startDate, endDate: endDate },
        });
    }

    _getRecordIds() {
        var self = this;
        return this._rpc({
            model: 'global.bluemaxpay.report',
            method: 'search_read',
            domain: this.domain,
            fields: ['transaction_id'],
        }).then(function(ids) {
            self.active_ids = ids;
        });
    }

    _reloadContent(groupby) {
        var self = this;
        return this._get_bluemaxpay_transactions(groupby).then(function(result) {
            self.state.bluemaxpay_transactions = result.bluemaxpay_transactions;
            self.state.groupby = result.groupby;
            self.state.results_months = self.results_months;
            self.state.results_days = self.results_days;
            self.state.sum = result.sum;
            self.state.results_years = self.results_years;
        });
    }

    _get_bluemaxpay_transactions(groupby) {
        var self = this;
        var domain = this.domain;
        return this.env.services.orm.call(
            'global.bluemaxpay.report',
            'get_bluemaxpay_transactions',
            [groupby],
        ).then(function(transactions) {
            self.bluemaxpay_transactions = transactions.bluemaxpay_transactions;
            self.groupby = transactions.groupby;
            self.sum = transactions.sum.toFixed(2);

            var i = 0;
            if (self.groupby == 'month') {
                var array_months = Array.from(new Set(transactions.bluemaxpay_transactions.map((x) => x['month'])))
                var resultArrayMonth = [];
                array_months.forEach(function(month) {
                    var records = self.bluemaxpay_transactions.filter(function(transaction) {
                        return transaction.month === month;
                    });

                    var totalAmount = records.reduce(function(acc, record) {
                        return acc + parseFloat(record.amount);
                    }, 0);

                    totalAmount = totalAmount.toFixed(2);
                    i += 1
                    resultArrayMonth.push({
                        id: i,
                        month: month,
                        totalAmount: totalAmount,
                        records: records
                    });
                });

                self.results_months = resultArrayMonth
            }
            if (self.groupby == 'day') {
                var array_days = Array.from(new Set(transactions.bluemaxpay_transactions.map((x) => x['day'])))
                var resultArrayday = [];
                array_days.forEach(function(day) {
                    var records = self.bluemaxpay_transactions.filter(function(transaction) {
                        return transaction.day === day;
                    });

                    var totalAmount = records.reduce(function(acc, record) {
                        return acc + parseFloat(record.amount);
                    }, 0);

                    totalAmount = totalAmount.toFixed(2);
                    i += 1

                    resultArrayday.push({
                        id: i,
                        day: day,
                        totalAmount: totalAmount,
                        records: records
                    });
                });
                self.results_days = resultArrayday
            }
            if (self.groupby == 'year') {
                var array_years = Array.from(new Set(transactions.bluemaxpay_transactions.map((x) => x['year'])))
                var resultArrayyear = [];
                array_years.forEach(function(year) {
                    var records = self.bluemaxpay_transactions.filter(function(transaction) {
                        return transaction.year === year;
                    });

                    var totalAmount = records.reduce(function(acc, record) {
                        return acc + parseFloat(record.amount);
                    }, 0);

                    totalAmount = totalAmount.toFixed(2);
                    i += 1

                    resultArrayyear.push({
                        id: i,
                        year: year,
                        totalAmount: totalAmount,
                        records: records
                    });
                });
                self.results_years = resultArrayyear
            }
            return transactions;
        });
    }


    _onClickGroupByMonth(ev) {
        ev.preventDefault();
        if (this.flag_month == false) {
            this._reloadContent('month')
            this.flag_month = true;
            this.flag_day = false;
            this.flag_year = false;
        } else {
            this._reloadContent(null)
            this.flag_month = false;
        }

    }
    _onClickMonth(ev) {
        ev.preventDefault();
        var monthHeader = $(ev.target).closest('thead').next().find('.month-record')
        monthHeader.map(function(index, tr) {
            if ($(tr).hasClass('d-none')) {
                $(tr).removeClass('d-none');
            } else {
                $(tr).addClass('d-none');
            }
        });
    }

    _onClickGroupByDay(ev) {
        ev.preventDefault();
        if (this.flag_day == false) {
            this._reloadContent('day')
            this.flag_day = true;
            this.flag_month = false;
            this.flag_year = false;
        } else {
            this._reloadContent(null)
            this.flag_day = false;
        }
    }
    _onClickDay(ev) {
        ev.preventDefault();
        var dayHeader = $(ev.target).closest('thead').next().find('.day-record')
        dayHeader.map(function(index, tr) {
            if ($(tr).hasClass('d-none')) {
                $(tr).removeClass('d-none');
            } else {
                $(tr).addClass('d-none');
            }
        });
    }

    _onClickGroupByYear(ev) {
        ev.preventDefault();
        if (this.flag_year == false) {
            this._reloadContent('year')
            this.flag_year = true;
            this.flag_day = false;
            this.flag_month = false;
        } else {
            this._reloadContent(null)
            this.flag_year = false;
        }
    }
    _onClickYear(ev) {
        ev.preventDefault();
        var yearHeader = $(ev.target).closest('thead').next().find('.year-record')
        yearHeader.map(function(index, tr) {
            if ($(tr).hasClass('d-none')) {
                $(tr).removeClass('d-none');
            } else {
                $(tr).addClass('d-none');
            }
        });
    }

    _onClickRecordLink(ev) {
        ev.preventDefault();
        return this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            res_model: $(ev.currentTarget).data('model'),
            res_id: $(ev.currentTarget).data('res-id'),
            views: [
                [false, 'form']
            ],
            target: 'current'
        });
    }

}

ClientAction.template = "global_report";
registry.category("actions").add('global_bluemaxpay_report_client_action', ClientAction);
return ClientAction;