from odoo import _, api, fields, models
from odoo.exceptions import UserError
import calendar

class GlobalBluemaxPayReport(models.Model):
    _name = 'global.bluemaxpay.report'
    _description = 'Bluemax Pay Transactions | Global Report'

    name = fields.Char('name')
    transaction_id = fields.Many2one(
        'bluemaxpay.transaction',
        string='Transaction ID',
        ondelete='restrict',
        required=True
    )

    @api.model
    def get_bluemaxpay_transactions(self, groupby=None):

        all_transaction_data = []
        bluemax_pay_data = self.env['bluemaxpay.transaction'].search([])
        for data in bluemax_pay_data:
            transaction_data = {
                'id': data.id if data.id else None,
                'name': data.name if data.name else None,
                'amount': "{:.2f}".format(data.amount),
                'date': data.date,
                'reference': data.reference if data.reference else None,
                'transaction_type': data.transaction_type,
                'partner_id': data.partner_id.name,
                'transaction_id': data.transaction_id.reference,
                'id_transaction': data.transaction_id.id,
                'transaction_model': 'payment.transaction',
                'data_id': data.id,
                'data_model': 'bluemaxpay.transaction',
                'name_id': data.sale_id.id if data.sale_id else data.move_id.id if data.move_id else data.payment_id.id,
                'name_model': 'sale.order' if data.sale_id else 'account.move' if data.move_id else 'account.payment',
                'state': dict(data._fields['state'].selection).get(data.state),
                'customer_id': data.partner_id.id
            }
            all_transaction_data.append(transaction_data)

        pos_module = self.env['ir.module.module'].search([('name', '=', 'point_of_sale')])
        pos_bluemax_module = self.env['ir.module.module'].search([('name', '=', 'pos_bluemax')])

        if pos_module.state == 'installed' and pos_bluemax_module.state =='installed':
            pos_payment_data = self.env['pos.payment'].search([('pos_payment_terminal','in',['card_not_present','card_present','bluemax','savedcards'])])
            if pos_payment_data:
                for data in pos_payment_data:
                    transaction_data = {
                        'name': data.pos_order_id.name,
                        'amount': "{:.2f}".format(data.amount),
                        'date': data.payment_date,
                        'reference': data.transaction_id if data.transaction_id else None,
                        'transaction_type': data.payment_method_id.name,
                        'partner_id': data.partner_id.name if data.partner_id else None,
                        'transaction_id': data.session_id.name if data.session_id else None,
                        'id_transaction': data.session_id.id if data.session_id else None,
                        'transaction_model': 'pos.session',
                        'data_id': data.id,
                        'data_model': 'pos.payment',
                        'name_id': data.pos_order_id.id if data.pos_order_id else None,
                        'name_model': 'pos.order' if data.pos_order_id else None,
                        'state': dict(data._fields['state'].selection).get(data.state) if 'state' in data._fields else None,
                        'customer_id': data.partner_id.id if data.partner_id else None
                    }
                    all_transaction_data.append(transaction_data)

        sorted_transactions = sorted(all_transaction_data, key=lambda x: x['date'] if x['date'] else '', reverse=True)

        sum = 0
        for rec in sorted_transactions:
            rec['month'] = calendar.month_name[rec['date'].month]
            rec['year'] = rec['date'].year
            rec['day'] = rec['date'].strftime("%d %b %Y")
            sum += float(rec['amount'])
        res = {
            'bluemaxpay_transactions': sorted_transactions,
            'groupby' : groupby,
            'sum' : sum
        }
        return res
