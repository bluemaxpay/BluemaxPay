# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class SendCustomSMSWizard(models.TransientModel):
    _name = 'send.custom.sms.wizard'
    _description = 'Send Custom SMS Wizard'

    def _get_default_sms_gateway(self):
        if not self.env.context.get('default_sms_gateway_id'):
            gateway_id = self.env['ir.config_parameter'].sudo().get_param('sms_gateway_kanak.sms_gateway')
            if gateway_id:
                return int(gateway_id)
        return False

    sms_gateway_id = fields.Many2one('sms.gateway', string='SMS Gateway', readonly=True, default=lambda x: x._get_default_sms_gateway())
    send_to = fields.Selection([('contact', 'Contact'), ('multiple_contacts', 'Multiple Contacts'), ('sms_group', 'SMS Group'), ('channel', 'Channel'), ('mobile', 'Mobile')], string='Send To', required=True, default="contact")
    partner_id = fields.Many2one('res.partner', 'Contact', domain=[('mobile', '!=', False)])
    partner_ids = fields.Many2many('res.partner', 'rel_partner_custom_sms_wiard', 'partner_id', 'custom_sms_wizard_id', string='Multiple Contacts', domain=[('mobile', '!=', False)])
    sms_group = fields.Many2one('sms.group', string='SMS Group')
    channel_id = fields.Many2one('discuss.channel', 'Channel')
    mobile = fields.Char(string='Mobile', help='With country code')
    from_mobile = fields.Char(string='From')
    message = fields.Text(string='Message', required=True)

    def _send_bulk_sms(self, mobiles):
        errors = []
        for mobile in mobiles:
            try:
                self.env['sms.gateway'].send_sms(self.message, mobile, self.sms_gateway_id)
            except:
                errors.append(mobile)
        if errors:
            raise UserError(_("SMS sending failure for the below mobile numbers:\n%s", '\n'.join([err for err in errors])))

    def send_sms(self):
        mobiles = []
        if self.send_to == 'mobile':
            # try:
            self.env['sms.gateway'].send_sms(self.message, self.mobile, self.sms_gateway_id)
            # except:
            #     raise UserError(_("SMS sending failed !"))

        elif self.send_to == 'contact':
            try:
                self.env['sms.gateway'].send_sms(self.message, self.partner_id.mobile, self.sms_gateway_id)
            except:
                raise UserError(_("SMS sending failed !"))

        elif self.send_to == 'multiple_contacts':
            mobiles += self.partner_ids.mapped('mobile')

        elif self.send_to == 'sms_group':
            if self.sms_group.recipient_type == 'odoo_contacts':
                for partner in self.sms_group.partner_ids:
                    mobiles.append(partner.mobile)
            else:
                recepients = self.env['sms.recepient'].search([('sms_group_ids', 'in', self.sms_group.ids)])
                mobiles += recepients.mapped('mobile')

        elif self.send_to == 'channel':
            if self.channel_id and self.channel_id.channel_last_seen_partner_ids:
                channel_partners = self.channel_id.channel_last_seen_partner_ids.filtered(lambda x: x.partner_id.mobile)
                mobiles += channel_partners.mapped('partner_id.mobile')

        if mobiles:
            self._send_bulk_sms(mobiles)
