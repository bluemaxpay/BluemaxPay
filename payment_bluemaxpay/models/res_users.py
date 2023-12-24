from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    bluemaxpay_trans_count = fields.Char(
        'BlueMax Pay token', compute="compute_count")

    def action_view_bluemaxpay_trans(self):
        print(self)
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'BlueMax Pay Token',
            'view_mode': 'tree,form',
            'res_model': 'bluemax.token',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': "{'create': True}"
        }

    def compute_count(self):
        """Compute custom clearance and account move's count"""
        for rec in self:
            if rec.env['bluemax.token'].search(
                    [('partner_id', '=', self.partner_id.id)]):
                rec.bluemaxpay_trans_count = rec.env['bluemax.token'].search_count(
                    [('partner_id', '=', self.partner_id.id)])
            else:
                rec.bluemaxpay_trans_count = 0
