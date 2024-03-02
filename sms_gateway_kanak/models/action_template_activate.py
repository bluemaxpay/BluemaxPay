from odoo import _
from odoo.exceptions import UserError


def action_template_activate(self):
    IrModel = self.env['ir.model']
    if self.flag == 'new_user' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Base module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)], limit=1)
        base_automation = self.create_base_automation({'trigger': 'on_create'})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='res.users', keywords=["name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'quotation_acknowledgement' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Sales module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)], limit=1)
        filter_domain = '[["state", "=", "sent"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='sale.order', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'so_confirm' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Sales module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)], limit=1)
        filter_domain = '[["state", "=", "sale"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='sale.order', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'so_cancel' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Sales module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)], limit=1)
        filter_domain = '[["state", "=", "cancel"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='sale.order', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'inv_created' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Invoicing module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', 'in', ['state', 'payment_state']), ('model_id', '=', model.id)])
        filter_domain = '["&", "&", ["state", "=", "posted"], ["payment_state", "=", "not_paid"], ["move_type", "=", "out_invoice"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='account.move', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'inv_payment_created' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Invoicing module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', 'in', ['state', 'payment_state']), ('model_id', '=', model.id)])
        filter_domain = '["&", "&", ["state", "=", "posted"], ["payment_state", "=", "paid"], ["move_type", "=", "out_invoice"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='account.move', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'bill_created' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Invoicing module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', 'in', ['state', 'payment_state']), ('model_id', '=', model.id)])
        filter_domain = '["&", "&", ["state", "=", "posted"], ["payment_state", "=", "not_paid"], ["move_type", "=", "in_invoice"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='account.move', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'credit_note_created' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Invoicing module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', 'in', ['state', 'payment_state']), ('model_id', '=', model.id)])
        filter_domain = '["&", "&", ["state", "=", "posted"], ["payment_state", "=", "not_paid"], ["move_type", "=", "out_refund"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='account.move', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'bill_refund_created' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Invoicing module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', 'in', ['state', 'payment_state']), ('model_id', '=', model.id)])
        filter_domain = '["&", "&", ["state", "=", "posted"], ["payment_state", "=", "not_paid"], ["move_type", "=", "in_refund"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='account.move', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'payment_tx_created' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Payment Acquirer module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)])
        filter_domain = '["&", ["state", "=", "done"], ["acquirer_reference", "!=", False]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='payment.transaction', keywords=["partner_id.name", "acquirer_reference"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'picking_ready' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Inventory module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)])
        filter_domain = '[["state", "=", "assigned"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='stock.picking', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'picking_done' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Inventory module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)])
        filter_domain = '[["state", "=", "done"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='stock.picking', keywords=["partner_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'pos_order_creation' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Point of Sale module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)])
        filter_domain = '[["state", "=", "paid"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='pos.order', keywords=["partner_id.name", "company_id.name", "name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'event_registration' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Event module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)])
        filter_domain = '[["state", "=", "open"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='event.registration', keywords=["partner_id.name", "event_id.name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'employee_birdthday' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Employees module is not installed !"))
        trg_date_id = self.env['ir.model.fields'].search([('name', '=', 'birthday'), ('model_id', '=', model.id)])
        filter_domain = '[["birthday", "!=", False]]'
        base_automation = self.create_base_automation({'trigger': 'on_time', 'filter_domain': filter_domain, 'trg_date_id': trg_date_id.id, 'trg_date_range': 9, 'trg_date_range_type': 'hour'})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='hr.employee', keywords=["name"]),
            'base_automation_id': base_automation.id
        })
    if self.flag == 'employee_payslip_paid' and not self.active:
        model = IrModel.search([('model', '=', self.model_flag)])
        if not model:
            raise UserError(_("Payroll module is not installed !"))
        trigger_field_ids = self.env['ir.model.fields'].search([('name', '=', 'state'), ('model_id', '=', model.id)])
        filter_domain = '[["state", "=", "paid"]]'
        base_automation = self.create_base_automation({'trigger': 'on_write', 'filter_domain': filter_domain, 'trigger_field_ids': [(6, 0, trigger_field_ids.ids)]})
        self.write({
            'active': True,
            'model_id': model.id,
            'keyword_lines': self.get_template_kw_data(model_name='hr.payslip', keywords=["date_from", "date_to", "name"]),
            'base_automation_id': base_automation.id
        })
