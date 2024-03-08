# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SMS_MARKETING_BUSINESS_MODELS = [
    'crm.lead',
    'event.registration',
    'hr.applicant',
    'res.partner',
    'event.track',
    'sale.order',
    'purchase.order',
    'account.move',
]


class SMSMarketing(models.Model):
    _name = 'sms.marketing'
    _description = 'SMS Marketing'

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def _group_expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    active = fields.Boolean(default=True, tracking=True)
    color = fields.Integer(string='Color Index')
    name = fields.Char(required=True)
    user_id = fields.Many2one('res.users', string='Responsible', tracking=True, readonly=True, default=lambda self: self.env.user)
    apply_on = fields.Selection([('sms_group', 'SMS Group'), ('model', 'Model')], string='Applies To', required=True, default='sms_group')
    sms_group = fields.Many2one('sms.group', string='SMS Group')
    model_id = fields.Many2one('ir.model', string='Model', domain=[('model', 'in', SMS_MARKETING_BUSINESS_MODELS)])
    model_real = fields.Char(compute='_compute_model', string='Recipients Real Model')
    model_name = fields.Char(related='model_id.model', string='Recipients Model Name', readonly=True, related_sudo=True)
    model_domain = fields.Char(string='Domain', default=[])
    body = fields.Text('SMS Body', required=True)
    sms_template_id = fields.Many2one('sms.gateway.template', string='SMS Template', ondelete='set null')
    auto_delete = fields.Boolean(string='Auto Delete')
    sent_date = fields.Datetime(string='Sent Date', copy=False)
    schedule_date = fields.Datetime(string='Scheduled for', tracking=True)
    sent_date = fields.Datetime(string='Sent Date', copy=False)
    state = fields.Selection([('draft', 'Draft'), ('in_queue', 'In Queue'), ('sending', 'Sending'), ('done', 'Sent')],
                             string='Status', required=True, tracking=True, copy=False, default='draft', group_expand='_group_expand_states')
    sms_force_send = fields.Boolean('Send Directly', help='Use at your own risks.')
    total = fields.Integer(compute="_compute_total")
    expected = fields.Integer(compute="_compute_statistics")
    sent = fields.Integer(compute="_compute_statistics")
    sending = fields.Integer(compute="_compute_statistics")
    failed = fields.Integer(compute="_compute_statistics")
    sent_ratio = fields.Integer(compute="_compute_statistics")
    sending_ratio = fields.Integer(compute="_compute_statistics")
    failed_ratio = fields.Integer(compute="_compute_statistics")
    next_departure = fields.Datetime(compute="_compute_next_departure", string='Scheduled date')

    @api.depends('model_id')
    def _compute_model(self):
        for record in self:
            record.model_real = record.model_name

    def _compute_total(self):
        for sms_marketing in self:
            sms_marketing.total = len(sms_marketing.sudo()._get_recipients())

    def _compute_statistics(self):
        """ Compute statistics of the sms marketing """
        self.env.cr.execute("""
            SELECT
                m.id as sms_marketing_id,
                COUNT(s.id) AS expected,
                COUNT(CASE WHEN s.state='queued' THEN 1 ELSE null END) AS sending,
                COUNT(CASE WHEN s.state='sent' OR s.state='delivered' THEN 1 ELSE null END) AS sent,
                COUNT(CASE WHEN s.state='failed' THEN 1 ELSE null END) AS failed
            FROM
                sms_history s
            RIGHT JOIN
                sms_marketing m
                ON (m.id = s.sms_marketing_id)
            WHERE
                m.id IN %s
            GROUP BY
                m.id
        """, (tuple(self.ids), ))
        for row in self.env.cr.dictfetchall():
            total = row['expected'] = (row['expected']) or 1
            row['sent_ratio'] = 100.0 * row['sent'] / total
            row['sending_ratio'] = 100.0 * row['sending'] / total
            row['failed_ratio'] = 100.0 * row['failed'] / total
            self.browse(row.pop('sms_marketing_id')).update(row)

    def _compute_next_departure(self):
        cron_next_call = self.env.ref('sms_gateway_kanak.ir_cron_sms_marketing_queue').sudo().nextcall
        str2dt = fields.Datetime.from_string
        cron_time = str2dt(cron_next_call)
        for sms_marketing in self:
            if sms_marketing.schedule_date:
                schedule_date = str2dt(sms_marketing.schedule_date)
                sms_marketing.next_departure = max(schedule_date, cron_time)
            else:
                sms_marketing.next_departure = cron_time

    @api.onchange('sms_template_id')
    def _onchange_sms_template_id(self):
        if self.sms_template_id:
            self.body = self.sms_template_id.body

    @api.model_create_multi
    def create(self, values_list):
        for values in values_list:
            if values.get('sms_template_id') and not values.get('body'):
                values['body'] = self.env['sms.template'].browse(values['sms_template_id']).body
        return super(SMSMarketing, self).create(values_list)

    def action_put_in_queue(self):
        self.write({'state': 'in_queue'})

    def action_put_in_queue_sms(self):
        res = self.action_put_in_queue()
        if self.sms_force_send:
            self.action_send_mail()
        return res

    def action_send_now_sms(self):
        if not self.sms_force_send:
            self.write({'sms_force_send': True})
        return self.action_send_sms()

    def action_cancel(self):
        self.write({'state': 'draft', 'schedule_date': False})

    def action_schedule(self):
        self.ensure_one()
        action = self.env.ref('sms_gateway_kanak.sms_marketing_schedule_date_date_action').read()[0]
        action['context'] = dict(self.env.context, default_sms_marketing_id=self.id)
        return action

    def action_retry_failed(self):
        failed_sms_history = self.env['sms.history'].sudo().search([
            ('sms_marketing_id', 'in', self.ids),
            ('state', 'in', ['failed', 'undelivered'])
        ])
        failed_sms_history.unlink()
        self.write({'state': 'in_queue'})

    def _get_recipients(self):
        res_ids = []
        if self.apply_on == 'model':
            if self.model_domain:
                domain = safe_eval(self.model_domain)
                try:
                    res_ids = self.env[self.model_real].search(domain).ids
                except ValueError:
                    res_ids = []
                    _logger.exception('Cannot get the sms marketing recipients, model: %s, domain: %s', self.model_real, domain)
            else:
                res_ids = []
        elif self.apply_on == 'sms_group' and self.sms_group:
            if self.sms_group.recipient_type == 'odoo_contacts' and self.sms_group.partner_ids:
                return self.sms_group.partner_ids
            elif self.sms_group.recipient_type == 'other_contacts' and self.sms_group.recipient_ids:
                return self.sms_group.recipient_ids
        return res_ids

    def _get_remaining_recipients(self):
        res_ids = self._get_recipients()
        if self.apply_on == 'sms_group':
            res_ids = res_ids.mapped('mobile')
            already_mailed = self.env['sms.history'].search_read([
                ('sms_marketing_id', 'in', self.ids),
                ('state', 'in', ['failed', 'undelivered'])], ['to_mobile'])
            done_res_ids = [record['to_mobile'] for record in already_mailed]
            return [rid for rid in res_ids if rid not in done_res_ids]
        else:
            already_mailed = self.env['sms.history'].search_read([
                ('sms_marketing_id', 'in', self.ids),
                ('state', 'in', ['failed', 'undelivered'])], ['res_id'])
            done_res_ids = [record['res_id'] for record in already_mailed]
            return [rid for rid in res_ids if rid not in done_res_ids]

    @api.model
    def _process_sms_marketing_queue(self):
        sms_marketings = self.search([('state', 'in', ('in_queue', 'sending')), '|', ('schedule_date', '<', fields.Datetime.now()), ('schedule_date', '=', False)])
        for sms_marketing in sms_marketings:
            user = sms_marketing.write_uid or self.env.user
            sms_marketing = sms_marketing.with_context(**user.with_user(user).context_get())
            if len(sms_marketing._get_remaining_recipients()) > 0:
                sms_marketing.state = 'sending'
                sms_marketing.action_send_sms()
            else:
                sms_marketing.write({'state': 'done', 'sent_date': fields.Datetime.now()})

    def _send_sms_get_composer_values(self, res_ids):
        return {
            'body': self.body,
            'template_id': self.sms_template_id.id,
            'res_model': res_ids[0]._name if self.apply_on == 'sms_group' else self.model_real,
            'res_ids': res_ids.ids if self.apply_on == 'sms_group' else repr(res_ids),
            'sms_marketing_id': self.id,
        }

    def action_send_sms(self, res_ids=None):
        for sms_marketing in self:
            if not res_ids:
                res_ids = sms_marketing._get_recipients()
            if not res_ids:
                raise UserError(_('There are no recipients selected.'))
            composer = self.env['sms.gateway.composer'].with_context(active_id=False).create(sms_marketing._send_sms_get_composer_values(res_ids))
            composer.action_send_sms()
            sms_marketing.write({'state': 'done', 'sent_date': fields.Datetime.now()})
        return True

    def action_view_sent(self):
        return self._action_view_documents_filtered('sent')

    def action_view_sending(self):
        return self._action_view_documents_filtered('sending')

    def action_view_failed(self):
        return self._action_view_documents_filtered('failed')

    def _action_view_documents_filtered(self, view_filter):
        if view_filter == 'sent':
            history = self.env['sms.history'].search([('state', 'in', ['sent', 'delivered']), ('sms_marketing_id', '=', self.id)])
        elif view_filter == ('sending'):
            history = self.env['sms.history'].search([('state', '=', 'queued'), ('sms_marketing_id', '=', self.id)])
        else:
            history = self.env['sms.history'].search([('state', 'in', ['undelivered', 'failed']), ('sms_marketing_id', '=', self.id)])

        return {
            'name': 'SMS History',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'sms.history',
            'domain': [('id', 'in', history.ids)],
            'context': dict(self._context, create=False)
        }
