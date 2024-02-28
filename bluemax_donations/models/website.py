# -*- coding: utf-8 -*-
# Powered by Kanak Infosystems LLP.
# © 2020 Kanak Infosystems LLP. (<https://www.kanakinfosystems.com>).

from odoo import models, fields


class Website(models.Model):

    _inherit = "website"

    send_email_from_donation_pay = fields.Boolean("Send Email from donation pay")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_email_from_donation_pay = fields.Boolean(related='website_id.send_email_from_donation_pay', readonly=False, default=False)
