# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class WebsiteCustomerScreen(http.Controller):
    @http.route(['/pos_screen_datas/<string:csession_id>'], auth="public", website=True, sitemap=True)
    def pos_screen_data(self, csession_id=None, **post):
        return request.render('pos_customer_screen.pos_screen_data', {'csession_id': csession_id})
