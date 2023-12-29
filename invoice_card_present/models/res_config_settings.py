
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    port = fields.Char('Port')
    ip_address = fields.Char('IPAddress')
    time_out = fields.Char('Time Out')
    version_num = fields.Char("Version Num")

    @api.model
    def get_values(self):
        """get values from the fields"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        port = params('invoice_card_present.port')
        ip_address = params('invoice_card_present.ip_address')
        time_out = params('invoice_card_present.time_out')
        version_num = params('invoice_card_present.version_num')
        res.update(
            port=port,
            ip_address=ip_address,
            time_out=time_out,
            version_num=version_num,
        )
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'invoice_card_present.port', self.port)
        self.env['ir.config_parameter'].sudo().set_param(
            'invoice_card_present.ip_address', self.ip_address)
        self.env['ir.config_parameter'].sudo().set_param(
            'invoice_card_present.time_out', self.time_out)
        self.env['ir.config_parameter'].sudo().set_param(
            'invoice_card_present.version_num', self.version_num)
