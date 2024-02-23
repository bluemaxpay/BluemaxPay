
from odoo import api, fields, models


class BlueMaxPayConfiguration(models.Model):
    _name = 'pax.terminal.configuration'
    _description = 'Pax Terminal Configuration'

    name = fields.Char('Terminal Name')
    port = fields.Char('Port')
    ip_address = fields.Char('IP Address')
    time_out = fields.Char('Time Out')
    version_num = fields.Char("Version Num")
    amount_pax = fields.Float("Pax Amount")
