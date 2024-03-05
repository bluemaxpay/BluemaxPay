/* @odoo-module */

import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class ExportDialog extends Component {
    static components = { Dialog };
    static props = ["close", "onExportConfirm"];
    static template = "payment_bluemaxpay.client_action.DatePickerPopup";

    get title() {
        return "Select Date Range For Export";
    }
}
