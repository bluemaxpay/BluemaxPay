from odoo.addons.pos_card_not_present import globalpayments as gp
from odoo.addons.pos_card_not_present.globalpayments.api.entities.enums import TransactionType


class BatchService(object):
    @staticmethod
    def close_batch(config_name='default'):
        _response = gp.api.builders.ManagementBuilder(
            TransactionType.BatchClose).execute(config_name)
        return gp.api.entities.BatchSummary()
