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

    def _compute_feature_support_fields(self):
        """ Override of `payment` to enable additional features. """
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == 'bluemaxpay').update({
            'support_manual_capture': True,
            'support_refund': 'partial',
            'support_tokenization': True,
        })

    def _get_bluemaxpay_urls(self):
        if self.state == 'enabled':
            return 'https://api2.heartlandportico.com'
        else:
            return 'https://cert.api2.heartlandportico.com'
