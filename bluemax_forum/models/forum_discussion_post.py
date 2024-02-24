# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import math
import re
from datetime import datetime
from odoo import SUPERUSER_ID, api, fields, models, tools, _
from odoo.addons.http_routing.models.ir_http import slug, unslug
from odoo.exceptions import UserError, ValidationError, AccessError
from odoo.osv import expression
from odoo.tools import sql

_logger = logging.getLogger(__name__)


class Post(models.Model):
    _name = 'discussion.forum.post'
    _description = 'Forum Post'
    _inherit = [
        'mail.thread',
        'website.seo.metadata',
        'website.searchable.mixin',
    ]

    name = fields.Char('Title')
    forum_id = fields.Many2one('discussion.forum', string='Forum', required=True)
    content = fields.Html('Content', strip_style=True)
    plain_content = fields.Text(
        'Plain Content',
        compute='_compute_plain_content', store=True)
    state = fields.Selection([('active', 'Active'), ('close', 'Closed')], string='Status', default='active')
    views = fields.Integer('Views', default=0, readonly=True, copy=False)
    active = fields.Boolean('Active', default=True)
    website_url = fields.Char('Website URL', compute='_compute_website_url')
    website_id = fields.Many2one(related='forum_id.website_id', readonly=True)
    parent_id = fields.Many2one(
        'discussion.forum.post', string='Question',
        ondelete='cascade', readonly=True, index=True)
    child_ids = fields.One2many(
        'discussion.forum.post', 'parent_id', string='Post Answers',
        domain="[('forum_id', '=', forum_id)]")
    last_activity_date = fields.Datetime(
        'Last activity on', readonly=True, required=True, default=fields.Datetime.now,
        help="Field to keep track of a post's last activity. Updated whenever it is replied to, "
             "or when a comment is added on the post or one of its replies."
    )
    child_count = fields.Integer('Answers', compute='_compute_child_count', store=True)
    is_locked = fields.Boolean(string="Is Locked")
    last_reply_uid = fields.Many2one('res.users', string="Last Reply user")
    reply_parent_id = fields.Many2one(
        'discussion.forum.post', string='Reply Parent')
    anchor = fields.Datetime(string="Anchor", default=fields.Datetime.now)
    closed_uid = fields.Many2one('res.users', string='Closed by', readonly=True, copy=False)
    closed_date = fields.Datetime('Closed on', readonly=True, copy=False)

    @api.depends('name')
    def _compute_website_url(self):
        self.website_url = False
        for post in self.filtered(lambda post: post.id):
            post.website_url = f'/discussion/forum/{slug(post.forum_id)}/{slug(post)}'

    def go_to_website(self):
        self.ensure_one()
        if not self.website_url:
            return False
        return self.env['website'].get_client_action(self.website_url)

    @api.depends('child_ids')
    def _compute_child_count(self):
        for post in self:
            post.child_count = len(post.child_ids)

    def _update_last_activity(self):
        self.ensure_one()
        return self.with_user(SUPERUSER_ID).write({'last_activity_date': fields.Datetime.now()})

    def _update_anchor_post(self):
        self.ensure_one()
        return self.with_user(SUPERUSER_ID).write({'anchor': fields.Datetime.now()})

    def _set_viewed(self):
        self.ensure_one()
        return sql.increment_fields_skiplock(self, 'views')

    def close(self):
        if any(post.parent_id for post in self):
            return False
        self.write({
            'state': 'close',
            'closed_uid': self._uid,
            'closed_date': datetime.today().strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
        })
        return True

    def reopen(self):
        if any(post.parent_id or post.state != 'close' for post in self):
            return False
        self.sudo().write({'state': 'active'})

    @api.model
    def _search_get_detail(self, website, order, options):
        with_description = options['displayDescription']
        with_date = options['displayDetail']
        search_fields = ['name']
        fetch_fields = ['id', 'name', 'website_url']
        mapping = {
            'name': {'name': 'name', 'type': 'text', 'match': True},
            'website_url': {'name': 'website_url', 'type': 'text', 'truncate': False},
        }

        domain = website.website_domain()
        domain = expression.AND([domain, [('state', '=', 'active')]])
        domain = expression.AND([domain, [('parent_id', '=', False)]])
        forum = options.get('forum')
        if forum:
            domain = expression.AND([domain, [('forum_id', '=', unslug(forum)[1])]])
        user = self.env.user

        # 'sorting' from the form's "Order by" overrides order during auto-completion
        order = options.get('sorting', order)
        if 'is_published' in order:
            parts = [part for part in order.split(',') if 'is_published' not in part]
            order = ','.join(parts)
        if with_description:
            search_fields.append('content')
            fetch_fields.append('content')
            mapping['description'] = {'name': 'content', 'type': 'text', 'html': True, 'match': True}
        if with_date:
            fetch_fields.append('write_date')
            mapping['detail'] = {'name': 'date', 'type': 'html'}
        return {
            'model': 'discussion.forum.post',
            'base_domain': [domain],
            'search_fields': search_fields,
            'fetch_fields': fetch_fields,
            'mapping': mapping,
            'icon': 'fa-comment-o',
            'order': order,
        }

    @api.model_create_multi
    def create(self, vals_list):
        posts = super(Post, self).create(vals_list)
        for post in posts:
            if post.parent_id and (post.parent_id.state == 'close' or post.parent_id.active is False):
                raise UserError(_('Posting Message on a [Deleted] or [Closed] post is not possible.'))
        return posts

    def write(self, vals):
        if 'active' in vals:
            if not self.user_has_groups('bluemax_forum.group_moderator'):
                raise AccessError(_('Moderator only can active or reactivate a post.'))
        if 'state' in vals:
            if not self.user_has_groups('bluemax_forum.group_moderator'):
                raise AccessError(_('Moderator only can close or repoen a post.'))
        if not self.user_has_groups('bluemax_forum.group_moderator') and self.create_uid.id != self.env.user.id:
            raise AccessError(_('Only edit own post only..'))
        res = super(Post, self).write(vals)
        return res

    def unlink(self):
        for post in self:
            if not self.user_has_groups('bluemax_forum.group_moderator') and post.create_uid.id != self.env.user.id:
                raise AccessError(_('Can not delete other post. you can only your own post delete'))
        return super(Post, self).unlink()
