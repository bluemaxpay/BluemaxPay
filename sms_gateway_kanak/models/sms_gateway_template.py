# -*- coding: utf-8 -*-
import ast

from odoo import api, fields, models, _
from odoo.addons.sms_gateway_kanak.models.action_template_activate import action_template_activate


class SMSGatewayTemplate(models.Model):
    _name = "sms.gateway.template"
    _description = 'SMS Gateway Templates'

    def _get_model_domain(self):
        domain = [('transient', '=', False)]
        return domain

    name = fields.Char('Name')
    active = fields.Boolean(default=True)
    model_flag = fields.Char(string='Model Flag')
    flag = fields.Char(string='Flag')
    model_id = fields.Many2one('ir.model', string='Applies to', domain=_get_model_domain,
                               help="The type of document this template can be used with")
    model = fields.Char('Related Document Model', related='model_id.model', index=True, store=True, readonly=True)
    body = fields.Text('Body', required=True)
    sidebar_action_id = fields.Many2one('ir.actions.act_window', 'Sidebar action', readonly=True, copy=False,
                                        help="Sidebar action to make this template available on records of the related document model")
    base_automation_id = fields.Many2one('base.automation', 'Automated Action', copy=False)
    keyword_lines = fields.One2many('sms.template.keyword.generator', 'sms_template', required=True)

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {}, name=_("%s (copy)") % self.name)
        return super(SMSGatewayTemplate, self).copy(default=default)

    def action_create_sidebar_action(self):
        ActWindow = self.env['ir.actions.act_window']
        view = self.env.ref('sms_gateway_kanak.sms_gateway_composer_view_form')
        for template in self:
            ctx = self.env.context.copy()
            ctx.update({'default_message': template.body})
            button_name = _('Send SMS (%s)') % template.name
            action = ActWindow.create({
                'name': button_name,
                'type': 'ir.actions.act_window',
                'res_model': 'sms.gateway.composer',
                'context': "{'default_template_id' : %d, 'default_composition_mode': 'guess', 'default_res_ids': active_ids, 'default_res_id': active_id}" % (template.id),
                'view_mode': 'form',
                'view_id': view.id,
                'target': 'new',
                'binding_model_id': template.model_id.id,
            })
            template.write({'sidebar_action_id': action.id})
        return True

    def action_unlink_sidebar_action(self):
        for template in self:
            if template.sidebar_action_id:
                template.sidebar_action_id.unlink()
        return True

    def unlink(self):
        self.sudo().mapped('sidebar_action_id').unlink()
        return super(SMSGatewayTemplate, self).unlink()

    def action_open_base_automated_action(self):
        self.ensure_one()
        return {
            'name': "Automated Action",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'base.automation',
            'res_id': self.base_automation_id.id
        }

    def action_template_activate(self):
        if self.flag and not self.active:
            action_template_activate(self)
        elif not self.active:
            self.active = True

    def get_template_kw_data(self, model_name, keywords):
        data = []
        for k in keywords:
            data.append((0, 0, {'model_name': model_name, 'field': '[["%s","=",1]]' % k}))
        return data

    def create_base_automation(self, data):
        model = self.env['ir.model'].search([('model', '=', self.model_flag)])
        data.update({
            'name': self.name,
            'model_id': model.id
        })
        base_automation = self.env['base.automation'].create(data)
        self.env['ir.actions.server'].create({
            'name': self.name,
            'model_id': model.id,
            'base_automation_id': base_automation.id,
            'state': 'sms_gateway',
            'sms_gateway_template_id': self.id
        })
        return base_automation

    def action_template_deactivate(self):
        if self.base_automation_id:
            action_server_id = False
            if self.base_automation_id.action_server_id:
                action_server_id = self.base_automation_id.action_server_id
            self.base_automation_id.unlink()
            if action_server_id:
                action_server_id.unlink()
        if self.keyword_lines:
            self.keyword_lines.unlink()
        self.active = False


class SMSTemplateKeywordGenerator(models.Model):
    _name = 'sms.template.keyword.generator'
    _description = 'SMS Template Keyword Generator'

    def _default_model_name(self):
        if self.env.context.get('model'):
            model_obj = self.env['ir.model'].browse(int(self.env.context.get('model')))
        return model_obj.model

    sms_template = fields.Many2one('sms.gateway.template')
    model_name = fields.Char(string='Model Name', default=lambda self: self._default_model_name())
    field = fields.Char(required=True)
    field_value = fields.Char(compute='compute_field_value')
    keyword = fields.Char(compute='compute_field_value')

    @api.depends('field')
    def compute_field_value(self):
        for rec in self:
            rec.field_value = False
            rec.keyword = False
            if rec.field:
                rec.field_value = (ast.literal_eval(rec.field)[0][0]).replace('.', ' > ')
                rec.keyword = "%" + ast.literal_eval(rec.field)[0][0] + "%"
