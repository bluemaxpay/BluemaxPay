# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SMSMarketingScheduleDate(models.TransientModel):
    _name = 'sms.marketing.schedule.date'
    _description = 'SMS Marketing Scheduling'

    schedule_date = fields.Datetime(string='Scheduled for')
    sms_marketing_id = fields.Many2one('sms.marketing', required=True, ondelete='cascade')

    @api.constrains('schedule_date')
    def _check_schedule_date(self):
        for scheduler in self:
            if scheduler.schedule_date < fields.Datetime.now():
                raise ValidationError(_('Please select a date equal/or greater than the current date.'))

    def set_schedule_date(self):
        self.sms_marketing_id.write({'schedule_date': self.schedule_date, 'state': 'in_queue'})
