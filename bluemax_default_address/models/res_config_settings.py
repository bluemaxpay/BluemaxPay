from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    set_enable_default_Country = fields.Boolean(
        string="Enable Default Customer Country",
        help="Enable to set default country for new partners.",
        readonly=False
    )

    set_enable_default_state = fields.Boolean(
        string="Enable Default Customer State",
        help="Enable to set default state for new partners.",
        readonly=False
    )

    set_enable_default_zip = fields.Boolean(
        string="Enable Default Customer ZIP",
        help="Enable to set default zip code for new partners.",
        readonly=False
    )

    set_enable_default_city = fields.Boolean(
        string="Enable Default Customer City",
        help="Enable to set default city for new partners.",
        readonly=False
    )


    set_default_country = fields.Many2one(
        'res.country',
        string="Set Default Customer Country",
        help="Select the default country for new partners.",
        readonly=False
    )

    set_default_state = fields.Many2one(
        'res.country.state',
        string="Set Default Customer State",
        help="Select the default state for new partners.",
        domain="[('country_id', '=', set_default_country)]",
        readonly=False
    )

    set_default_zip = fields.Char(
        string="Set Default Customer ZIP",
        help="Enter the default ZIP code for new partners.",
        readonly=False
    )

    set_default_city = fields.Char(
        string="Set Default Customer City",
        help="Enter the default City for new partners.",
        readonly=False
    )



class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_default_Country = fields.Boolean(
        string="Enable Default Customer Country",
        related="company_id.set_enable_default_Country",
        help="Enable to set default country for new partners.",
        readonly=False
    )

    enable_default_state = fields.Boolean(
        string="Enable Default Customer State",
        related="company_id.set_enable_default_state",
        help="Enable to set default state for new partners.",
        readonly=False
    )

    enable_default_zip = fields.Boolean(
        string="Enable Default Customer ZIP",
        related="company_id.set_enable_default_zip",
        help="Enable to set default zip code for new partners.",
        readonly=False
    )

    enable_default_city = fields.Boolean(
        string="Enable Default Customer City",
        related="company_id.set_enable_default_city",
        help="Enable to set default city for new partners.",
        readonly=False
    )

    set_default_country = fields.Many2one(
        'res.country',
        string="Set Default Customer Country",
        related="company_id.set_default_country",
        help="Select the default country for new partners.",
        readonly=False
    )

    set_default_state = fields.Many2one(
        'res.country.state',
        string="Set Default Customer State",
        related="company_id.set_default_state",
        domain="[('country_id', '=', set_default_country)]",
        help="Select the default state for new partners.",
        readonly=False
    )

    set_default_zip = fields.Char(
        string="Set Default Customer ZIP",
        related="company_id.set_default_zip",
        help="Enter the default ZIP code for new partners.",
        readonly=False
    )


    set_default_city = fields.Char(
        string="Set Default Customer City",
        related="company_id.set_default_city",
        help="Enter the default City for new partners.",
        readonly=False
    )

