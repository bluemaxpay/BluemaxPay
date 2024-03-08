# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models


class DiscussChannel(models.Model):
    _inherit = 'discuss.channel'

    use_for_incm_sms = fields.Boolean("Use for Incoming SMS ?")
