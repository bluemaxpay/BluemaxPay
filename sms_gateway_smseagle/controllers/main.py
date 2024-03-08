# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

import logging
import pprint
from datetime import datetime

from odoo import http, SUPERUSER_ID
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class SMSEagleController(http.Controller):
    _webhook_url = '/incoming/smseagle/message'

    @http.route(_webhook_url, type='http', auth='public', csrf=False)
    def smseagle_incoming_message(self, **post):
        _logger.info('SMSEagle: get message as %s', pprint.pformat(post))
        if post.get('sender'):
            env = request.env(user=SUPERUSER_ID, su=True)
            subtype_id = env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')
            partner = request.env['res.partner'].sudo().search([('incm_mobile_subs', 'ilike', post.get('sender'))])
            if partner:
                message = env['mail.message'].create([{
                    'date': datetime.strptime(post.get('timestamp'), '%Y%m%d%H%M%S'),
                    'author_id': SUPERUSER_ID,
                    'message_type': 'sms',
                    'subtype_id': subtype_id,
                    'model': 'res.partner',
                    'res_id': partner.id,
                    'body': post.get('text')
                }])
                notif_create_values = [{
                    'author_id': SUPERUSER_ID,
                    'mail_message_id': message.id,
                    'notification_status': 'sent',
                    'notification_type': 'sms',
                    'res_partner_id': partner.id
                }]
                env['mail.notification'].sudo().create(notif_create_values)
            else:
                channel = env['discuss.channel'].search([('use_for_incm_sms', '=', True)], limit=1)
                if channel:
                    message = env['mail.message'].create([{
                        'date': datetime.strptime(post.get('timestamp'), '%Y%m%d%H%M%S'),
                        'author_id': SUPERUSER_ID,
                        'message_type': 'sms',
                        'subtype_id': subtype_id,
                        'model': 'discuss.channel',
                        'res_id': channel.id,
                        'body': post.get('text')
                    }])
        return Response("OK", status=200)
