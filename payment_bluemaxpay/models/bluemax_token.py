from odoo import models, fields


class BlueMaxPayToken(models.Model):
    _name = 'bluemax.token'
    _description = 'bluemaxpay token'

    name = fields.Char()
    token = fields.Char(readonly=True, default='')
    partner_id = fields.Many2one('res.partner', required=True)
    active = fields.Boolean(default=True)

    country_id = fields.Many2one(
        comodel_name='res.country', string='Country')
    customer_country_id = fields.Many2one(
        comodel_name='res.country',
        string="Customer Country",
        store=True, readonly=False)
    customer_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string="Customer State",
        # domain="[('country_id', '=', customer_country_id)]",
        store=True, readonly=False)
    customer_city = fields.Char(
        string="Customer City",
        store=True, readonly=False)
    customer_street = fields.Char(
        string="Customer Street",
        store=True, readonly=False)
    customer_zip = fields.Char(
        string="Customer Zip",
        store=True, readonly=False)

    def create_token(self):

        company = self.env.user.company_id
        country_id = False
        state_id = False
        zip = False
        city = False
        
        if hasattr(company, 'set_enable_default_Country') and company.set_enable_default_Country:
            if hasattr(company, 'set_default_country') and company.set_default_country:
                country_id = company.set_default_country.id
        if hasattr(company, 'set_enable_default_state') and company.set_enable_default_state:
            if hasattr(company, 'set_default_state') and company.set_default_state:
                state_id = company.set_default_state.id
        if hasattr(company, 'set_enable_default_zip') and company.set_enable_default_zip:
            if hasattr(company, 'set_default_zip') and company.set_default_zip:
                zip = company.set_default_zip
        if hasattr(company, 'set_enable_default_city') and company.set_enable_default_city:
            if hasattr(company, 'set_default_city') and company.set_default_city:
                city = company.set_default_city

        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Token',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'bluemaxpay.token',
            'context': {
                'default_token_id': self.id,
                'default_customer_city': city,
                'default_customer_state_id': state_id,
                'default_customer_zip': zip,
                'default_customer_country_id': country_id,
            }
        }
