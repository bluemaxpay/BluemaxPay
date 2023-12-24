from odoo import fields, models, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_pos_payment(self):
        result = {'search_params': {'fields': []}}
        result['search_params']['fields'].extend(['transaction_id', 'approved_amount', 'cardholder_name',
                                                  'auth_code', 'avs_resp', 'href', 'device_id', 'transaction',
                                                  'bluemaxpay_response', 'ref_number', 'pos_order_id', 'payment_method_id', 'card_type', 'card_number'])
        return result

    def _loader_params_bluemax_token(self):
        result = {'search_params': {'fields': []}}
        result['search_params']['fields'].append('partner_id')
        result['search_params']['fields'].append('token')
        result['search_params']['fields'].append('name')
        return result

    def _loader_params_pos_payment_method(self):
        result = super()._loader_params_pos_payment_method()
        result['search_params']['fields'].append('developer_id')
        result['search_params']['fields'].append('version_number')
        result['search_params']['fields'].append('secret_api_key',)
        result['search_params']['fields'].append('public_api_key')
        result['search_params']['fields'].append('enable_card_details')
        result['search_params']['fields'].append('state')
        return result

    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        result.extend(['bluemax.token', 'pos.payment'])
        return result

    def _get_pos_ui_bluemax_token(self, params):
        return self.env['bluemax.token'].search_read(**params['search_params'])

    def _get_pos_ui_pos_payment(self, params):
        return self.env['pos.payment'].search_read(**params['search_params'])

    def _get_pos_ui_pos_payment_method(self, params):
        return self.env['pos.payment.method'].search_read(**params['search_params'])
