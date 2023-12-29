from odoo import fields, models, api


class BlueMaxPayToken(models.Model):
    _name = 'bluemax.token'
    _description = 'bluemaxpay token'

    name = fields.Char()
    token = fields.Char(readonly=True, default='')
    partner_id = fields.Many2one('res.partner', required=True)
    active = fields.Boolean(default=True)

    def create_token(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create token',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'bluemaxpay.token',
            'context': {
                'default_token_id': self.id
            }
        }
