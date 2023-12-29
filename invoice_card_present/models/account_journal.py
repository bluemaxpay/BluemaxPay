# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    # def _default_outbound_payment_methods(self):
    #     res = super()._default_outbound_payment_methods()
    #     if self._is_payment_method_available('bluemaxpay_card_present'):
    #         res |= self.env.ref(
    #             'invoice_card_present.account_payment_method_card_present')
    #     return res
