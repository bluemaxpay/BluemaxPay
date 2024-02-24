# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.addons.http_routing.models.ir_http import url_for

class Website(models.Model):
    _inherit = 'website'

    def _search_get_details(self, search_type, order, options):
        result = super()._search_get_details(search_type, order, options)
        if search_type in ['forums', 'forums_only', 'all']:
            result.append(self.env['discussion.forum']._search_get_detail(self, order, options))
        if search_type in ['forums', 'forum_posts_only', 'all']:
            result.append(self.env['discussion.forum.post']._search_get_detail(self, order, options))
        return result

    def get_user_rank_logs(self, user):
        ranks = self.env['rank.type'].sudo().search([], order='target_posts DESC')
        url = None
        for rec in ranks:
            if rec.target_posts > 1:
                if user.user_post_count >= rec.target_posts or  user.user_reply_count >= rec.target_posts:
                    url = '/web/content/rank.type/%s/logo' %(rec.id)
                    break
        return url