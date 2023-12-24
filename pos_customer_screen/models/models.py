# -*- coding: utf-8 -*-


from odoo import fields, models, api


class ImBus(models.Model):
    _inherit = 'bus.bus'

    @api.model
    def sendposdata(self, user_id=None, data=None):
        user_id = self.env['res.users'].sudo().browse(user_id)
        notifications = []
        notifications.append([user_id.partner_id, 'pos_screen_order_datas', data])
        self.sudo()._sendmany(notifications)


class PosConfig(models.Model):
    _inherit = 'pos.config'

    customer_screen_user_id = fields.Many2one('res.users', string="Customer Screen User")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_screen_user_id = fields.Many2one(related='pos_config_id.customer_screen_user_id', readonly=False)
