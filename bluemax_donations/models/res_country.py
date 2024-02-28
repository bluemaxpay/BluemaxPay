# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import re
from odoo import models


class ResCountry(models.Model):
    _inherit = 'res.country'

    def get_donation_address_fields(self):
        self.ensure_one()
        return re.findall(r'\((.+?)\)', self.address_format)

    def get_website_donation_countries(self, mode='billing'):
        res = self.sudo().search([])
        return res

    def get_website_donation_states(self):
        res = self.sudo().state_ids
        return res
