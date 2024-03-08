# -*- coding: utf-8 -*-

from odoo import fields, models


class SMSGroup(models.Model):
    _name = 'sms.group'
    _description = 'SMS Group'

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    active = fields.Boolean(default=True, tracking=True)
    name = fields.Char(string='Group Name', required=True)
    recipient_type = fields.Selection([('odoo_contacts', 'Odoo Contacts'), ('other_contacts', 'Other Contacts')], string='Recipient Type', required=True, default="odoo_contacts")
    recipient_ids = fields.Many2many('sms.recepient', 'rel_recipient_sms_group', 'sms_group_id', 'recipient_id')
    partner_ids = fields.Many2many('res.partner', 'rel_partner_sms_group', 'sms_group_id', 'partner_id', domain=[('mobile', '!=', False)])
    recipients_count = fields.Integer(compute='compute_recipients_count', string='Total Recipients')

    def compute_recipients_count(self):
        for rec in self:
            rec.recipients_count = 0
            if rec.recipient_type == 'odoo_contacts':
                rec.recipients_count = len(rec.partner_ids)
            else:
                rec.recipients_count = len(rec.recipient_ids)

    def action_open_recipients(self):
        self.ensure_one()
        context = dict(self.env.context, default_sms_group_ids=self.ids)
        if self.recipient_type == 'other_contacts':
            return {
                'name': 'Recipients',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'sms.recepient',
                'domain': [('sms_group_ids', 'in', self.ids)],
                'context': context
            }
        return False


class SMSRecepient(models.Model):
    _name = 'sms.recepient'
    _description = 'SMS Recipient'
    _rec_name = 'mobile'

    sms_group_ids = fields.Many2many('sms.group', 'rel_recipient_sms_group', 'recipient_id', 'sms_group_id', string='SMS Groups', domain=[('recipient_type', '=', 'other_contacts')])
    mobile = fields.Char(required=True)
    name = fields.Char()
    email = fields.Char()


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sms_group_ids = fields.Many2many('sms.group', 'rel_partner_sms_group', 'partner_id', 'sms_group_id', string='SMS Groups', domain=[('recipient_type', '=', 'odoo_contacts')])
