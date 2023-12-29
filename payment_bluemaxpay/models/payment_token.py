import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    def _handle_reactivation_request(self):
        super()._handle_reactivation_request()
        if self.code != 'bluemaxpay':
            return
        _logger.error(
            _("Saved payment methods cannot be restored once they have been deleted."))
        raise UserError(
            _("Saved payment methods cannot be restored once they have been deleted."))
