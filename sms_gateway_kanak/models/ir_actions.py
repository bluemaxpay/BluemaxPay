# -*- coding: utf-8 -*-

from odoo import fields, models


class ServerActions(models.Model):
    _name = 'ir.actions.server'
    _inherit = ['ir.actions.server']

    DEFAULT_PYTHON_CODE = """# Available variables:
#  - env: Odoo Environment on which the action is triggered
#  - model: Odoo Model of the record on which the action is triggered; is a void recordset
#  - record: record on which the action is triggered; may be void
#  - records: recordset of all records on which the action is triggered in multi-mode; may be void
#  - time, datetime, dateutil, timezone: useful Python libraries
#  - log: log(message, level='info'): logging function to record debug information in ir.logging table
#  - Warning: Warning Exception to use with raise
#  - To return an action, assign: action = {...}\n
#  - To Send SMS(Custom Gateway) using sms gateway template try below code:\n
#  env['sms.gateway'].send_sms(message, mobile, gateway, record, sender, partner_id, template, sms_marketing)
#  - NOTE: message: Text message, mobile: receiver's mobile number, gateway: gateway object or False, record: record object,
#          sender: sender mobile number or False, partner_id: contact id or False, template: sms gateway template object or False, sms_marketing: sms marketing object or False

\n\n\n\n"""

    state = fields.Selection(selection_add=[
        ('sms_gateway', 'Send SMS(Custom Gateway)')
    ], ondelete={'sms_gateway': 'set default'})
    sms_gateway_template_id = fields.Many2one('sms.gateway.template', ondelete='set null', domain="[('model_id', '=', model_id)]")
    code = fields.Text(string='Python Code', groups='base.group_system',
                       default=DEFAULT_PYTHON_CODE,
                       help="Write Python code that the action will execute. Some variables are "
                            "available for use; help about python expression is given in the help tab.")

    def _run_action_sms_gateway_multi(self, eval_context=None):
        if not self.sms_gateway_template_id or self._is_recompute():
            return False

        records = eval_context.get('records') or eval_context.get('record')
        if not records:
            return False

        composer = self.env['sms.gateway.composer'].with_context(
            default_res_model=records._name,
            default_res_ids=records.ids,
            default_template_id=self.sms_gateway_template_id.id,
        ).create({})
        composer.action_send_sms()
        return False
