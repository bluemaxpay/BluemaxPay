from odoo import api, fields, models


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields):
        defaults = super(Partner, self).default_get(fields)
        company = self.env.user.company_id
        if company.set_enable_default_Country:
            if 'country_id' not in defaults and company.set_default_country:
                defaults['country_id'] = company.set_default_country.id
        if company.set_enable_default_state:
            if 'state_id' not in defaults and company.set_default_state:
                defaults['state_id'] = company.set_default_state.id
        if company.set_enable_default_zip:
            if 'zip' not in defaults and company.set_default_zip:
                defaults['zip'] = company.set_default_zip
        if company.set_enable_default_city:
            if 'city' not in defaults and company.set_default_city:
                defaults['city'] = company.set_default_city
        return defaults
