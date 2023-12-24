from odoo import fields, models


class BluemaxPosPayment(models.Model):
    _name = "bluemax.pos.payment"
    _description = "Bluemax POS Payment"

    order_id = fields.Char('Order ID', required=True)
    amount = fields.Float(required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True)
    payment_method_id = fields.Many2one(
        'pos.payment.method', string='POS Payment Method', required=True)
    state = fields.Selection([('draft', 'Draft'), ('success', 'Success'),
                              ('failed', 'Failed')], string='Status', default='draft')
    transactionId = fields.Char(string="Bluemax Transaction ID")
    cardholderName = fields.Char()
    deviceResponseCode = fields.Char(string="Response Code")
    deviceResponseMessage = fields.Char()
    responseText = fields.Char()
    maskedCardNumber = fields.Char(string="Card Number")
    card_type = fields.Char(string="Card Type")
    terminalRefNumber = fields.Char(string="Ref. Number")
    approvalcode = fields.Char(string="Authcode")
    entrymode = fields.Char(string="Entry")
    transactionAmount = fields.Char()
    approvedAmount = fields.Char()
    applicationName = fields.Char()
    applicationId = fields.Char()

    def create_bluemax_payment(self, data):
        data.update({'currency_id': self.env.ref(
            'base.%s' % data.get('currency_id')).id})
        record = self.create(data)
        return record.id
