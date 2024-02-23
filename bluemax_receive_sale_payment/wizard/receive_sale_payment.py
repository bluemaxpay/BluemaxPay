from odoo import fields, models, api, _


# class AccountPaymentRegisterInherit(models.TransientModel):
#     _inherit = 'account.payment.register'

#     @api.model
#     def _get_payment_method_selection(self):
#         payment_methods = self.env['sale.payment.methods'].search([], order='sequence')
#         selection = [('bluemaxpay_sale', 'Bluemax Pay'),('bluemaxpay_card_present', 'Bluemax Pay Card Present')]
#         selection += [(method.id, method.payment_method_line_id.name) for method in payment_methods]
#         # selection += [(method.name, method.name) for method in payment_methods]
#         return selection

#     payment_method = fields.Selection(selection='_get_payment_method_selection', required=True, default='bluemaxpay_sale')
#     journal_id = fields.Many2one(
#         comodel_name='account.journal',
#         compute='_compute_journal_id', store=True, readonly=True, precompute=True,
#         domain="[('id', 'in', available_journal_ids)]")
    
#     @api.onchange('payment_method')
#     def _get_fixed_journal(self):
#         if self.payment_method != 'bluemaxpay_sale' and self.payment_method != 'bluemaxpay_card_present':
#             self.journal_id = self.env['sale.payment.methods'].search([('id','=',self.payment_method)]).journal_id.id
#             self.payment_method_line_id = self.env['sale.payment.methods'].search([('id','=',self.payment_method)]).payment_method_line_id.id

#             # self.journal_id = self.env['sale.payment.methods'].search([('name','=',self.payment_method)]).journal_id.id

#         if self.payment_method == 'bluemaxpay_sale':
#             payment_method_line = self.env['account.payment.method.line'].search([
#                 ('payment_type', '=', 'inbound'),
#                 ('code', '=', 'bluemaxpay'),
#                 ('company_id', '=', self.env.user.company_id.id)
                
#             ])
#             if payment_method_line:
#                 self.journal_id = payment_method_line[0].journal_id.id
#                 self.payment_method_line_id = payment_method_line[0].id
#             # else:
#             #     self.journal_id = False
#             #     self.payment_method_line_id = False

#         if self.payment_method == 'bluemaxpay_card_present':
#             payment_method_line = self.env['account.payment.method.line'].search([
#                 ('payment_type', '=', 'inbound'),
#                 ('code', '=', 'bluemaxpay_card_present'),
#                 ('company_id', '=', self.env.user.company_id.id)
#             ])
#             if payment_method_line:
#                 self.journal_id = payment_method_line[0].journal_id.id
#                 self.payment_method_line_id = payment_method_line[0].id









            # else:
            #     self.journal_id = False
            #     self.payment_method_line_id = False

    # def _create_payments(self):
    #     self.ensure_one()
    #     batches = self._get_batches()
    #     first_batch_result = batches[0]
    #     edit_mode = self.can_edit_wizard and (
    #         len(batches[0]['lines']) == 1 or self.group_payment)
    #     to_process = []
    #     if edit_mode:
    #         payment_vals = self._create_payment_vals_from_wizard(
    #             first_batch_result)
    #         to_process.append({
    #             'create_vals': payment_vals,
    #             'to_reconcile': batches[0]['lines'],
    #             'batch': batches[0],
    #         })
    #     else:
    #         # Don't group payments: Create one batch per move.
    #         if not self.group_payment:
    #             new_batches = []
    #             for batch_result in batches:
    #                 for line in batch_result['lines']:
    #                     new_batches.append({
    #                         **batch_result,
    #                         'lines': line,
    #                     })
    #             batches = new_batches

    #         for batch_result in batches:
    #             to_process.append({
    #                 'create_vals': self._create_payment_vals_from_batch(batch_result),
    #                 'to_reconcile': batch_result['lines'],
    #                 'batch': batch_result,
    #             })
    #     payments = self._init_payments(to_process, edit_mode=edit_mode)
    #     self._post_payments(to_process, edit_mode=edit_mode)
    #     if self.is_bluemaxpay:
    #         bluemaxpay = self.env['bluemaxpay.transaction'].search([('name', '=', self.communication), ('state', '=', 'post')],
    #                                                                limit=1)
    #         if bluemaxpay.state == 'post':
    #             payments.state = 'posted'
    #             transaction = self.env['payment.transaction'].search(
    #                 [('reference', '=', self.communication)])
    #             transaction.provider_reference = bluemaxpay.reference
    #             if not transaction:
    #                 transaction = self.env['payment.transaction'].create({
    #                     'provider_id': self.env.ref('payment_bluemaxpay.payment_acquirer_bluemaxpay').id,
    #                     'reference': self.communication,
    #                     'provider_reference': bluemaxpay.reference,
    #                     'partner_id': self.partner_id.id,
    #                     'payment_id': payments.id,
    #                     'amount': self.amount,
    #                     'currency_id': self.currency_id.id,
    #                     'state': 'draft',
    #                     'bluemaxpay_trans_id': bluemaxpay.id,
    #                     'captured_amount': bluemaxpay.captured_amount
    #                 })
    #             transaction._set_done()
    #             bluemaxpay.transaction_id = transaction.id


    #     self._reconcile_payments(to_process, edit_mode=edit_mode)
    #     if not self.is_bluemaxpay:
    #         sale_payment_method = self.env['sale.payment.methods'].search([('name','=',self.payment_method)])
    #         payments.sale_payment_method = sale_payment_method.id
    #     return payments

class SalePaymentConfirm(models.Model):
    _inherit = 'sale.order.payment'

    @api.model
    def _get_payment_method_selection(self):
        payment_methods = self.env['sale.payment.methods'].search([], order='sequence')
        selection = [('bluemaxpay_sale', 'Bluemax Pay')]
        selection += [(method.id, method.payment_method_line_id.name) for method in payment_methods]
        return selection

    payment_method = fields.Selection(selection='_get_payment_method_selection', required=True, default='bluemaxpay_sale')
    journal_id = fields.Many2one('account.journal', string="Journal",readonly=True)
    date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)
    ref = fields.Char(string='Memo', copy=False)

    @api.onchange('payment_method')
    def _get_fixed_journal(self):
        if self.payment_method != 'bluemaxpay_sale':
            self.journal_id = self.env['sale.payment.methods'].search([('id','=',self.payment_method)]).journal_id.id

    def create_payment(self):
        if self.payment_method == 'bluemaxpay_sale':
            return super(SalePaymentConfirm, self).create_payment()
        else:
            sale_payment_method = self.env['sale.payment.methods'].search([('id','=',self.payment_method)])
            self.journal_id = self.env['sale.payment.methods'].search([('id','=',self.payment_method)]).journal_id.id
            sale = self.env['sale.order'].browse(self.env.context.get('active_id'))
            sale_line_id = self.env['account.payment'].create({
                                'date': self.date,
                                'ref': self.ref,
                                'partner_id': self.partner_id.id,
                                'partner_type': 'customer',
                                'amount': self.amount,
                                'journal_id': self.journal_id.id,
                                'payment_method_line_id': sale_payment_method.payment_method_line_id.id,
                                # 'sale_payment_method': sale_payment_method.id
                            })
            sale_line_id.action_post()
            self.sale_id.message_post(body=_(
                            "A %s Journal Transaction for %.2f has been created as : %s (Manual)." % (self.journal_id.name, self.amount, sale_line_id.name)))
            return 
