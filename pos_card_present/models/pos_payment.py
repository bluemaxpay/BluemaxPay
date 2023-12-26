from odoo import fields, models
from odoo.exceptions import UserError
from globalpayments.api.entities import Transaction
from globalpayments.api.entities.exceptions import ApiException
import logging
_logger = logging.getLogger(__name__)


class PosPayment(models.Model):
    """Interit to add fields for stripe payment terminals """
    _inherit = "pos.payment"

    bluemaxpay_transaction = fields.Char(
        string="BlueMax Transaction ID:", required=False, )
    refunded_id = fields.Char(string="BlueMax Refund ID", required=False, )

    def pos_void(self):
        try:
            if self.transaction_id:
                void_transaction = Transaction.from_id(self.transaction_id) \
                    .void() \
                    .execute()
            else:
                raise UserError('BlueMax Pay Transaction does not exist')
        except ApiException as e:
            _logger.error(e)
            raise UserError(e)
