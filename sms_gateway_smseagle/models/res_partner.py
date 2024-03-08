# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    incm_mobile_subs = fields.Char("Incoming Mobile Subscriptions")
