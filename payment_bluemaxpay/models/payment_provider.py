from odoo import fields, models


class HeartlandPayment(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(selection_add=[('bluemaxpay', "BlueMax Pay")], ondelete={'bluemaxpay': 'set default'})
    secret_api_key = fields.Char(string="Secret Api Key", required_if_provider='benefitpay', groups='base.group_user')
    public_api_key = fields.Char(string="Public Api Key", required_if_provider='benefitpay', groups='base.group_user')
    license_id = fields.Char(required_if_provider='benefitpay', groups='base.group_user')
    device_id = fields.Char(required_if_provider='benefitpay', groups='base.group_user')
    username = fields.Char(required_if_provider='benefitpay', groups='base.group_user')
    password = fields.Char(required_if_provider='benefitpay', groups='base.group_user')
    developer_id = fields.Char('Developer ID', required_if_provider='benefitpay', groups='base.group_user')
    version_number = fields.Char(required_if_provider='benefitpay', groups='base.group_user')
    payment_type = fields.Selection([
        ('authorize', 'Authorize'), ('capture', 'Authorize and Capture')], required_if_provider='benefitpay',
        groups='base.group_user', default='capture')
    enable_pdf_payment = fields.Boolean(string="Add Payment Link in Sales Report")

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'bluemaxpay').update({
            'support_manual_capture': 'full_only',
            'support_refund': 'partial',
            'support_tokenization': True,
        })

    def _get_bluemaxpay_urls(self):
        if self.state == 'enabled':
            return 'https://api2.heartlandportico.com'
        else:
            return 'https://cert.api2.heartlandportico.com'

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        default_codes = super()._get_default_payment_method_codes()
        if self.code != 'bluemaxpay':
            return default_codes
        return ['bluemaxpay']
