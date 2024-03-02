# -*- coding: utf-8 -*-
import ast
import re
import json
from babel.dates import format_date
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class SMSGateway(models.Model):
    _name = 'sms.gateway'
    _description = 'SMS Gateway'

    def _valid_field_parameter(self, field, name):
        return name == 'required_if_gateway' or super()._valid_field_parameter(field, name)

    def get_bar_graph_datas(self):
        data = []
        date_dict = {}
        graph_title = ""
        graph_key = "Sent SMS"
        locale = get_lang(self.env).code
        today = datetime.today()
        last_month = today + timedelta(days=-15)

        def build_graph_data(date, value):
            # display date in locale format
            short_name = format_date(date, 'd MMM', locale=locale)
            return {'label': short_name, 'value': value, 'type': 'o_sample_data'}

        query = """
            SELECT
                l.date,
                COUNT(CASE WHEN l.state='sent' OR l.state='delivered' THEN 1 ELSE null END) AS sent
            FROM sms_history l
            WHERE l.sms_gateway = %s
                AND l.date > %s
                AND l.date <= %s
            GROUP BY l.date
            ORDER BY l.date
        """
        self.env.cr.execute(query, (self.id, last_month, today))
        query_results = self.env.cr.dictfetchall()
        for val in query_results:
            date = val['date'].date()
            if date != today.strftime(DF):  # make sure the last point in the graph is today
                date_data = build_graph_data(date, val['sent'])
                if date_dict.get(date_data['label']):
                    date_dict[date_data['label']] += date_data['value']
                else:
                    date_dict.update({date_data['label']: date_data['value']})
        for k, v in date_dict.items():
            data.append({'label': k, 'value': v, 'type': 'o_sample_data'})
        return [{'values': data, 'title': graph_title, 'key': graph_key, 'is_sample_data': False}]

    def _kanban_dashboard_graph(self):
        for sms in self:
            sms.kanban_dashboard_graph = json.dumps(sms.get_bar_graph_datas())

    name = fields.Char('Name', required=True, translate=True)
    color = fields.Integer('Color', compute='_compute_color', store=True)
    display_as = fields.Char('Displayed as', translate=True, help="How the acquirer is displayed to the customers.")
    sequence = fields.Integer('Sequence', default=10, help="Determine the display order")
    gateway = fields.Selection(
        selection=[('manual', 'Custom')], string='Gateway',
        default='manual', required=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company.id, required=True)
    state = fields.Selection([
        ('disabled', 'Disabled'),
        ('enabled', 'Enabled'),
        ('test', 'Test Mode')], required=True, default='disabled', copy=False,
        help="""In test mode, a test sms is sent through a test
             sms gateway. This mode is advised when setting up the
             sms gateway. Watch out, test and production modes require
             different credentials.""")
    image_128 = fields.Image("Image", max_width=128, max_height=128)
    module_id = fields.Many2one('ir.module.module', string='Corresponding Module')
    module_state = fields.Selection(related='module_id.state')
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graph')

    @api.depends('state', 'module_state')
    def _compute_color(self):
        for sms_gateway in self:
            if sms_gateway.module_id and not sms_gateway.module_state == 'installed':
                sms_gateway.color = 4  # blue
            elif sms_gateway.state == 'disabled':
                sms_gateway.color = 3  # yellow
            elif sms_gateway.state == 'test':
                sms_gateway.color = 2  # orange
            elif sms_gateway.state == 'enabled':
                sms_gateway.color = 7  # green

    def _check_required_if_gateway(self):
        """ If the field has 'required_if_gateway="<gateway>"' attribute, then it
        required if record.gateway is <gateway>. """
        field_names = []
        enabled_acquirers = self.filtered(lambda acq: acq.state in ['enabled', 'test'])
        for k, f in self._fields.items():
            gateway = getattr(f, 'required_if_gateway', None)
            if gateway and any(
                acquirer.gateway == gateway and not acquirer[k]
                for acquirer in enabled_acquirers
            ):
                ir_field = self.env['ir.model.fields']._get(self._name, k)
                field_names.append(ir_field.field_description)
        if field_names:
            raise ValidationError(_("Required fields not filled: %s") % ", ".join(field_names))
        
    @api.model_create_multi
    def create(self, vals_list):
        records = super(SMSGateway, self).create(vals_list)
        for record in records:
            record._check_required_if_gateway()
        return records
    def write(self, vals):
        result = super(SMSGateway, self).write(vals)
        self._check_required_if_gateway()
        return result

    def send_sms(self, message, mobile, gateway=False, record=False, sender=False, partner_id=False, template=False, sms_marketing=False):
        if not gateway:
            gateway_id = self.env['ir.config_parameter'].sudo().get_param('sms_gateway_kanak.sms_gateway')
            if not gateway_id:
                raise UserError(_("There is no default sms gateway selected in configuration !"))
            gateway = self.browse(int(gateway_id))
        if hasattr(gateway, '%s_send_sms' % gateway.gateway):
            if template and record:
                message = self.get_msg_by_keyword_mapping(record, template, template.body)
            sms_data = getattr(gateway, '%s_send_sms' % gateway.gateway)(message, mobile, gateway, record, sender, partner_id, sms_marketing)
            self.create_sms_history(sms_data)
            return sms_data
        return False

    def create_sms_history(self, data):
        sms_history = self.env['sms.history'].sudo().create({
            'sms_gateway': data.get('sms_gateway'),
            'partner_id': data.get('partner_id'),
            'from_mobile': data.get('from_mobile'),
            'to_mobile': data.get('to_mobile'),
            'message': data.get('message'),
            'sms_reference': data.get('sms_reference'),
            'res_model': data.get('res_model'),
            'res_id': data.get('res_id'),
            'sms_marketing_id': data.get('sms_marketing_id'),
            'updated_date': data.get('updated_date'),
            'state': data.get('status'),
            'error_message': data.get('error_message') or ''
        })
        return sms_history

    def gateway_status_callback(self, data, gateway):
        feedback_method_name = '_%s_sms_status_validate' % gateway
        if hasattr(self, feedback_method_name):
            return getattr(self, feedback_method_name)(data)
        return True

    def action_send_custom_sms(self):
        return {
            'name': 'Send SMS',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'send.custom.sms.wizard',
            'target': 'new'
        }

    def _get_fields_values(self, record, field):
        relation = field.split('.')
        if record:
            for r in relation:
                record = getattr(record, r)
        return record

    def get_msg_by_keyword_mapping(self, record, template, msg):
        pattern = "%(.*?)%"
        keywords = re.findall(pattern, msg)
        for keyword in keywords:
            line = template.keyword_lines.filtered(lambda x: x.keyword == "%" + keyword + "%")
            if line.field:
                field = ast.literal_eval(line.field)[0][0]
                value = self._get_fields_values(record, field)
                msg = msg.replace("%" + keyword + "%", str(value))
        return msg

    def open_history_graph_view(self):
        return {
            'name': 'SMS History Graph View',
            'type': 'ir.actions.act_window',
            'view_type': 'graph',
            'view_mode': 'graph',
            'res_model': 'sms.history',
            'context': {'search_default_sms_gateway': self.id}
        }
