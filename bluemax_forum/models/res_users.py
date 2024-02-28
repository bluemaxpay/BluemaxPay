# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ResUsers(models.Model):
    _inherit = 'res.users'

    user_post_count = fields.Integer(string="User Post Count", compute="_compute_user_posts")
    user_reply_count = fields.Integer(string="User reply post Count", compute="_compute_user_posts")

    def _compute_user_posts(self):
        for rec in self:
            rec.user_post_count = self.env['discussion.forum.post'].search_count([('create_uid', '=', rec.id)])
            rec.user_reply_count = self.env['discussion.forum.post'].search_count([('create_uid', '=', rec.id), ('parent_id', '!=', False)])