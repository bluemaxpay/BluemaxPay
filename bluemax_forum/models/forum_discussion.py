# -*- coding: utf-8 -*-

import textwrap
from collections import defaultdict
from operator import itemgetter

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.addons.http_routing.models.ir_http import slug
from odoo.tools.translate import html_translate


class DiscussionForum(models.Model):
    _name = 'discussion.forum'
    _description = 'Discussion Forum'
    _inherit = [
        'mail.thread',
        'image.mixin',
        'website.seo.metadata',
        'website.multi.mixin',
        'website.searchable.mixin',
    ]
    _order = "sequence, id"

    name = fields.Char('Forum Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=1)
    active = fields.Boolean(default=True)
    post_ids = fields.One2many('discussion.forum.post', 'forum_id', string='Posts')
    last_post_id = fields.Many2one('discussion.forum.post', compute='_compute_last_post_id')
    post_count = fields.Integer(string="Post Count", compute="_compute_post_count")
    post_reply_counts = fields.Integer(string="Post Reply Count", compute="_compute_post_count")
    post_total_views_counts = fields.Integer(string="Post views Count", compute="_compute_post_count")
    total_posts = fields.Integer('# Posts', compute='_compute_forum_statistics')
    total_views = fields.Integer('# Views', compute='_compute_forum_statistics')

    @api.depends('post_ids.state', 'post_ids.views', 'post_ids.child_count')
    def _compute_forum_statistics(self):
        default_stats = {'total_posts': 0, 'total_views': 0}

        if not self.ids:
            self.update(default_stats)
            return

        result = {cid: dict(default_stats) for cid in self.ids}
        read_group_res = self.env['discussion.forum.post']._read_group(
            [('forum_id', 'in', self.ids), ('state', 'in', ('active', 'close')), ('parent_id', '=', False)],
            ['forum_id'],
            ['__count', 'views:sum'])
        for forum, count, views_sum in read_group_res:
            stat_forum = result[forum.id]
            stat_forum['total_posts'] += count
            stat_forum['total_views'] += views_sum
        for record in self:
            record.update(result[record.id])

    def _compute_website_url(self):
        if not self.id:
            return False
        return f'/discussion/forum/{slug(self)}'

    def go_to_website(self):
        self.ensure_one()
        website_url = self._compute_website_url()
        if not website_url:
            return False
        return self.env['website'].get_client_action(self._compute_website_url())

    @api.depends('post_ids')
    def _compute_post_count(self):
        for rec in self:
            rec.post_count = len(rec.post_ids.filtered(lambda x: not x.parent_id))
            rec.post_reply_counts = len(rec.post_ids.filtered(lambda x: x.parent_id))
            rec.post_total_views_counts = sum(rec.post_ids.filtered(lambda x: not x.parent_id).mapped('views'))
