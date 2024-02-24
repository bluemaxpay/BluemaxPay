import re
from datetime import datetime

from odoo import api, fields, models, tools, _

class RankType(models.Model):
	_name = 'rank.type'
	_description = "Rank"

	name = fields.Char(string="Name")
	logo = fields.Image(string="Logo")
	target_posts = fields.Integer(string="Target Posts (created/reply)", default=0)
