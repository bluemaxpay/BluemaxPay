from odoo import fields, models


class WSPartner(models.Model):
    _inherit = "res.partner"

    bluemax_partner_ids = fields.One2many('bluemax.token', 'partner_id', 'Saved Card')
