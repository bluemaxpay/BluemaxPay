# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import datetime
import json
import pprint
import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SMSGateway(models.Model):
    _inherit = 'sms.gateway'

    gateway = fields.Selection(selection_add=[('smseagle', 'SMSEagle')], ondelete={'smseagle': 'set default'})
    smseagle_access_token = fields.Char(string='Access Token', required_if_gateway='smseagle', groups='base.group_user')
    smseagle_test_mobile = fields.Char(required_if_gateway='smseagle', groups='base.group_user')

    def _get_smseagle_urls(self):
        return "https://sms.bluemaxpay.com"

    def send_smseagle_test_sms(self):
        self.ensure_one()
        url = self._get_smseagle_urls()
        headers = {
            'content-type': "application/json",
            'access-token': self.smseagle_access_token
        }
        payload = {
            "to": [self.smseagle_test_mobile],
            "text": "Test SMS from Odoo"
        }
        response = requests.post(url + "/index.php/api/v2/messages/sms", data=json.dumps(payload), headers=headers)
        res = response.json()
        if response.status_code == 200:
            title = _("Test Succeeded!")
            message = _("Test SMS has been sent to %s" % self.smseagle_test_mobile)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': title,
                    'message': message,
                    'sticky': False,
                }
            }
        raise UserError(_("Connection Test Failed!\nError code: %s" % pprint.pformat(res)))

    def smseagle_send_sms(self, message, mobile, gateway=False, record=False, partner_id=False, sender=False, sms_marketing=False):
        url = self._get_smseagle_urls()
        headers = {
            'content-type': "application/json",
            'access-token': self.smseagle_access_token
        }
        payload = {
            "to": [mobile],
            "text": message
        }
        response = requests.post(url + "/index.php/api/v2/messages/sms", data=json.dumps(payload), headers=headers)
        res = response.json()
        if response.status_code != 200:
            res.update({'error_message': res})
        res = res[0]
        res.update({
            'sms_gateway': self.id,
            'partner_id': partner_id or False,
            'to_mobile': res.get('number') or mobile,
            'message': message,
            'sms_reference': res.get('id'),
            'updated_date': datetime.datetime.strptime(res.get('date_updated'), "%a, %d %b %Y %H:%M:%S +0000") if res.get('date_updated') else False,
            'sms_marketing_id': sms_marketing.id if sms_marketing else False,
            'state': res.get('status'),
            'res_model': False,
            'res_id': False
        })
        if record:
            res.update({'res_model': record._name, 'res_id': record.id})
        if response.status_code != 200:
            res.update({'body': message, 'status': 'failed'})
        return res

    @api.model
    def update_smseagle_status(self):
        smswagle_gateway = self.env['sms.gateway'].search([('gateway', '=', 'smseagle'), ('state', '=', 'enabled')], limit=1)
        smss = self.env['sms.history'].search([('sms_gateway', '=', smswagle_gateway.id), ('state', '=', 'queued')])
        for sms in smss:
            url = smswagle_gateway._get_smseagle_urls()
            headers = {
                'content-type': "application/json",
                'access-token': smswagle_gateway.smseagle_access_token
            }
            response = requests.get(url + "/api/v2/messages/status/%s" % sms.sms_reference, headers=headers)
            res = response.json()
            if response.status_code == 200:
                status = res.get('status')
                folder = res.get('folder')

                if status == 'SendingOKNoReport' and folder == 'sentitems':
                    sms.write({'state': 'sent'})
