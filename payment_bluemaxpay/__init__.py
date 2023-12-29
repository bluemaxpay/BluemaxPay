from . import models
from . import controllers
from . import wizard
from odoo.addons.payment import setup_provider, reset_payment_provider


def post_init_hook(cr):
    setup_provider(cr, 'bluemaxpay')


def uninstall_hook(cr):
    reset_payment_provider(cr, 'bluemaxpay')
