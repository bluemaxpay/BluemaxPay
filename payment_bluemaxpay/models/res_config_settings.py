
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_type = fields.Selection([('authorize', 'Authorize'), ('capture', 'Authorize and Capture')],
                                    default='capture')
    secret_api_key = fields.Char('Secret Api Key')
    developer_id = fields.Char('Developer')
    version_number = fields.Char('Version Number')

    @api.model
    def get_values(self):
        """get values from the fields"""
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo().get_param
        payment_type = params('payment_bluemaxpay.payment_type') or 'capture'
        res.update(
            payment_type=payment_type,
        )
        return res

    def set_values(self):
        """Set values in the fields"""
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'payment_bluemaxpay.payment_type', self.payment_type)
