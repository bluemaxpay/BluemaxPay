
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.web import Home
from odoo.addons.website_sale.controllers.main import WebsiteSale


class Website(Home):
    @http.route('/', type='http', auth="public", website=True, sitemap=True)
    def index(self, **kw):
        """Home Page"""
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            if order.state == 'sale':
                order.cart_quantity = 0

        return super(Website, self).index()


class BlueMaxPayWebsiteSale(WebsiteSale):

    @http.route(['/shop/confirmation'], type='http', auth="public", website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """Shop payment confirmation"""
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            if order.state == 'sale':
                order.cart_quantity = 0
            return request.render("website_sale.confirmation", {
                'order': order,
                'order_tracking_info': self.order_2_return_dict(order),
            })
        else:
            return request.redirect('/shop')

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            if order.state == 'sale':
                order.cart_quantity = 0
        return super(BlueMaxPayWebsiteSale, self).shop()

    @http.route(['/shop/<model("product.template"):product>'], type='http', auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        sale_order_id = request.session.get('sale_last_order_id')
        if sale_order_id:
            order = request.env['sale.order'].sudo().browse(sale_order_id)
            if order.state == 'sale':
                order.cart_quantity = 0

        return request.render("website_sale.product", self._prepare_product_values(product, category, search, **kwargs))
