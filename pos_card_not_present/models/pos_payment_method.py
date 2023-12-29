from odoo import fields, models, api
from odoo.addons.pos_card_not_present.globalpayments.api import ServicesConfig, ServicesContainer
from odoo.addons.pos_card_not_present.globalpayments.api.payment_methods import CreditCardData
from odoo.addons.pos_card_not_present.globalpayments.api.entities import Address
from odoo.addons.pos_card_not_present.globalpayments.api.entities.exceptions import ApiException
from odoo.addons.pos_card_not_present.globalpayments.api.payment_methods import CreditCardData


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'
    _description = 'Payment method'

    def _get_payment_terminal_selection(self):
        return super(PosPaymentMethod, self)._get_payment_terminal_selection() + [('card_not_present', 'Card Not present')] + [('savedcards', 'Saved Cards Only')]

    developer_id = fields.Char('Developer ID')
    version_number = fields.Char(string="Version No.")
    secret_api_key = fields.Char(string="Secret Api Key")
    public_api_key = fields.Char(string="Public Api Key")
    enable_card_details = fields.Boolean(
        string='Enable Card details On Receipt',
        required=False)
    state = fields.Selection(
        string='State',
        selection=[('enabled', 'Live'),
                   ('test', 'Test'), ],
        required=False, )

    def payment_card_not_present(self, payload, amount):
        """Card not present: payment"""
        print(payload, amount)
        config = ServicesConfig()
        config.secret_api_key = self.secret_api_key
        config.developer_id = self.developer_id
        config.version_number = self.version_number

        if self.state == 'enabled':
            config.service_url = 'https://api2.heartlandportico.com'
        else:
            config.service_url = 'https://cert.api2.heartlandportico.com'
        ServicesContainer.configure(config)
        card = CreditCardData()
        if payload['is_token']:
            token = self.env['bluemax.token'].browse(
                int(payload['token']))
            card.token = token.token
        else:
            print('no token')
            card.number = payload['number']
            card.exp_month = payload['month']
            card.exp_year = payload['year']
            card.cvn = payload['cvv']
            card.card_holder_name = payload['name']
        address = Address()
        address.postal_code = '12345'
        try:
            response = card.charge(amount).with_currency(
                self.env.company.currency_id.name).with_address(address).execute()
            print(response.__dict__)
            return {
                'response_code': response.response_code,
                'reference_number': response.reference_number,
                'transaction_id': response.transaction_id,
                'response_message': response.response_message,
                'reference_number': response.reference_number,
                'auth_code': response.transaction_reference.auth_code,
                'avs_response_message': response.avs_response_message,
                'card_type': response.card_type,
                'response': response
            }
        except ApiException as e:
            print(e)
            return e
