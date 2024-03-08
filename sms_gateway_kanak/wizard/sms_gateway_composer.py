# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SMSGatewayComposer(models.TransientModel):
    _name = 'sms.gateway.composer'
    _description = 'Send Gateway Composer'

    @api.model
    def default_get(self, fields):
        result = super(SMSGatewayComposer, self).default_get(fields)
        if fields == 'partner_ids':
            return result

        result['res_model'] = result.get('res_model') or self.env.context.get('active_model')

        if not result.get('res_id'):
            if not result.get('res_ids') and self.env.context.get('active_id'):
                result['res_id'] = self.env.context.get('active_id')
        if not result.get('res_ids'):
            if not result.get('res_id') and self.env.context.get('active_ids'):
                result['res_ids'] = repr(self.env.context.get('active_ids'))

        if result['res_model']:
            result.update(
                self._get_composer_values(result['res_model'], result.get('res_id'), result.get('body'), result.get('template_id'))
            )
        return result

    res_model = fields.Char('Document Model Name')
    res_id = fields.Integer('Document ID')
    res_ids = fields.Char('Document IDs')
    # recipients
    recipient_valid_count = fields.Integer('# Valid recipients', compute='_compute_recipients', compute_sudo=False)
    recipient_invalid_count = fields.Integer('# Invalid recipients', compute='_compute_recipients', compute_sudo=False)
    number_field_name = fields.Char(string='Field holding number')
    numbers = fields.Char('Recipients (Numbers)')
    sanitized_numbers = fields.Char('Sanitized Number', compute='_compute_sanitized_numbers', compute_sudo=False)
    partner_ids = fields.Many2many('res.partner')
    # content
    template_id = fields.Many2one('sms.gateway.template', string='Use Template', domain="[('model', '=', res_model)]")
    sms_marketing_id = fields.Many2one('sms.marketing', string='SMS Marketing')
    body = fields.Text('Message', required=True)

    def _sms_get_partner_fields(self):
        fields = []
        if not self.res_model and not self.res_ids:
            obj = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        else:
            obj = self.env[self.res_model].browse(literal_eval(self.res_ids))
        if hasattr(obj, 'partner_id'):
            fields.append('partner_id')
        if hasattr(obj, 'partner_ids'):
            fields.append('partner_ids')
        return fields

    def _sms_get_default_partners(self):
        partners = self.env['res.partner']
        if not self.res_model and not self.res_ids:
            obj = self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids'))
        else:
            obj = self.env[self.res_model].browse(literal_eval(self.res_ids))
        for fname in self._sms_get_partner_fields():
            partners |= obj.mapped(fname)
        if partners:
            return partners
        elif 'employee_id' in obj._fields:
            return obj.employee_id

    def _sms_get_number_fields(self):
        return ['mobile', 'phone', 'work_phone', 'work_mobile']

    def _sms_get_recipients_info(self, records, force_field=False, partner_fallback=True):
        result = dict.fromkeys(records.ids, False)
        tocheck_fields = [force_field] if force_field else self._sms_get_number_fields()
        for record in records:
            all_numbers = [record[fname] for fname in tocheck_fields if fname in record]
            all_partners = record._mail_get_partners()[record.id]

            valid_number, fname = False, False
            for fname in [f for f in tocheck_fields if f in record]:
                valid_number = record._phone_format(fname=fname)
                if valid_number:
                    break

            if valid_number:
                result[record.id] = {
                    'partner': all_partners[0] if all_partners else self.env['res.partner'],
                    'sanitized': valid_number,
                    'number': record[fname],
                    'partner_store': False,
                    'field_store': fname,
                }
            elif all_partners and partner_fallback:
                partner = self.env['res.partner']
                for partner in all_partners:
                    for fname in self.env['res.partner']._phone_get_number_fields():
                        valid_number = partner._phone_format(fname=fname)
                        if valid_number:
                            break

                if not valid_number:
                    fname = 'mobile' if partner.mobile else ('phone' if partner.phone else 'mobile')

                result[record.id] = {
                    'partner': partner,
                    'sanitized': valid_number if valid_number else False,
                    'number': partner[fname],
                    'partner_store': True,
                    'field_store': fname,
                }
            else:
                # did not find any sanitized number -> take first set value as fallback;
                # if none, just assign False to the first available number field
                value, fname = next(
                    ((value, fname) for value, fname in zip(all_numbers, tocheck_fields) if value),
                    (False, tocheck_fields[0] if tocheck_fields else False)
                )
                result[record.id] = {
                    'partner': self.env['res.partner'],
                    'sanitized': False,
                    'number': value,
                    'partner_store': False,
                    'field_store': fname
                }
        return result

    @api.depends('numbers', 'res_model', 'res_id')
    def _compute_sanitized_numbers(self):
        for composer in self:
            if composer.numbers:
                record = composer._get_records() if composer.res_model and composer.res_id else self.env.user
                numbers = [number.strip() for number in composer.numbers.split(',')]
                sanitized_numbers = [record._phone_format(number=number) for number in numbers]
                invalid_numbers = [number for sanitized, number in zip(sanitized_numbers, numbers) if not sanitized]
                if invalid_numbers:
                    raise UserError(_('Following numbers are not correctly encoded: %s', repr(invalid_numbers)))
                composer.sanitized_numbers = ','.join(sanitized_numbers)
            else:
                composer.sanitized_numbers = False

    @api.depends('res_model', 'res_id', 'res_ids', 'number_field_name', 'sanitized_numbers')
    def _compute_recipients(self):
        for composer in self:
            composer.recipient_valid_count = 0
            composer.recipient_invalid_count = 0

            if not composer.res_model:
                continue

            records = composer._get_records()
            if records:
                res = self._sms_get_recipients_info(records, force_field=composer.number_field_name)
                composer.recipient_valid_count = len([rid for rid, rvalues in res.items() if rvalues['sanitized']])
                composer.recipient_invalid_count = len([rid for rid, rvalues in res.items() if not rvalues['sanitized']])
            else:
                composer.recipient_invalid_count = 0 if (
                    composer.sanitized_numbers
                ) else 1

    @api.onchange('res_model', 'res_id', 'template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.body = self.template_id.body

    # ------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------

    def action_send_sms(self):
        if self.recipient_invalid_count:
            raise UserError(_('%s invalid recipients') % self.recipient_invalid_count)
        self.send_sms()
        return False

    def send_sms(self):
        Gateway = self.env['sms.gateway']
        records = self._get_records()
        all_recipients = self._sms_get_recipients_info(records, force_field=self.number_field_name)
        for record in records:
            recipients = all_recipients[record.id]
            sanitized = recipients['sanitized']
            if sanitized:
                receiver = sanitized if sanitized else recipients['number']
                try:
                    Gateway.send_sms(self.body, receiver, False, record, False, recipients['partner'].id, self.template_id, self.sms_marketing_id)
                except:
                    raise UserError(_("SMS sending failed !"))
        return True

    # ------------------------------------------------------------
    # Tools
    # ------------------------------------------------------------

    def _get_composer_values(self, res_model, res_id, body, template_id):
        result = {}
        template = self.env['sms.gateway.template'].browse(template_id)
        result['body'] = template.body
        return result

    def _get_records(self):
        if not self.res_model:
            return None
        elif self.res_ids:
            records = self.env[self.res_model].browse(literal_eval(self.res_ids or '[]'))
        else:
            records = self.env[self.res_model].browse(self.res_id)
        return records
