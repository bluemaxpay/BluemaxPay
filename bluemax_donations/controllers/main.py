# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.tools.json import scriptsafe as json_safe

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.controllers import portal as payment_portal


class PaymentPortal(payment_portal.PaymentPortal):

    @http.route(
        '/website/payment/pay', type='http', methods=['GET'], auth='public', website=True, sitemap=False,
    )
    def website_payment_pay(
        self, reference=None, amount=None, currency_id=None, partner_id=None, company_id=None,
        access_token=None, **kwargs
    ):
        currency_id, partner_id, company_id = tuple(map(
            self._cast_as_int, (currency_id, partner_id, company_id)
        ))
        amount = self._cast_as_float(amount)

        # Raise an HTTP 404 if a partner is provided with an invalid access token
        if partner_id:
            if not payment_utils.check_access_token(access_token, partner_id, amount, currency_id):
                raise werkzeug.exceptions.NotFound()  # Don't leak information about ids.

        user_sudo = request.env.user
        logged_in = not user_sudo._is_public()
        # If the user is logged in, take their partner rather than the partner set in the params.
        # This is something that we want, since security rules are based on the partner, and created
        # tokens should not be assigned to the public user. This should have no impact on the
        # transaction itself besides making reconciliation possibly more difficult (e.g. The
        # transaction and invoice partners are different).
        partner_is_different = False
        if logged_in:
            partner_is_different = partner_id and partner_id != user_sudo.partner_id.id
            partner_sudo = user_sudo.partner_id
        else:
            partner_sudo = request.env['res.partner'].sudo().browse(partner_id).exists()
            if not partner_sudo:
                return request.redirect(
                    # Escape special characters to avoid loosing original params when redirected
                    f'/web/login?redirect={urllib.parse.quote(request.httprequest.full_path)}'
                )

        # Instantiate transaction values to their default if not set in parameters
        reference = reference or payment_utils.singularize_reference_prefix(prefix='tx')
        amount = amount or 0.0  # If the amount is invalid, set it to 0 to stop the payment flow
        company_id = company_id or partner_sudo.company_id.id or user_sudo.company_id.id
        company = request.env['res.company'].sudo().browse(company_id)
        currency_id = currency_id or company.currency_id.id

        # Make sure that the currency exists and is active
        currency = request.env['res.currency'].browse(currency_id).exists()
        if not currency or not currency.active:
            raise werkzeug.exceptions.NotFound()  # The currency must exist and be active.

        # Select all the payment methods and tokens that match the payment context.
        providers_sudo = request.env['payment.provider'].sudo()._get_compatible_providers(
            company_id, partner_sudo.id, amount, currency_id=currency.id, **kwargs
        )  # In sudo mode to read the fields of providers and partner (if logged out).
        payment_methods_sudo = request.env['payment.method'].sudo()._get_compatible_payment_methods(
            providers_sudo.ids,
            partner_sudo.id,
            currency_id=currency.id,
        )  # In sudo mode to read the fields of providers.
        tokens_sudo = request.env['payment.token'].sudo()._get_available_tokens(
            providers_sudo.ids, partner_sudo.id
        )  # In sudo mode to be able to read tokens of other partners and the fields of providers.
        # Make sure that the partner's company matches the company passed as parameter.
        company_mismatch = not PaymentPortal._can_partner_pay_in_company(partner_sudo, company)

        # Generate a new access token in case the partner id or the currency id was updated
        access_token = payment_utils.generate_access_token(partner_sudo.id, amount, currency.id)

        portal_page_values = {
            'res_company': company,  # Display the correct logo in a multi-company environment.
            'company_mismatch': company_mismatch,
            'expected_company': company,
            'partner_is_different': partner_is_different,
        }
        payment_form_values = {
            'show_tokenize_input_mapping': PaymentPortal._compute_show_tokenize_input_mapping(
                providers_sudo, **kwargs
            ),
        }
        payment_context = {
            'reference_prefix': reference,
            'amount': amount,
            'currency': currency,
            'partner_id': partner_sudo.id,
            'providers_sudo': providers_sudo,
            'payment_methods_sudo': payment_methods_sudo,
            'tokens_sudo': tokens_sudo,
            'transaction_route': '/payment/transaction',
            'landing_route': '/payment/confirmation',
            'access_token': access_token,
        }
        rendering_context = {
            **portal_page_values,
            **payment_form_values,
            **payment_context,
            **self._get_custom_extra_payment_form_values(
                **payment_context, currency_id=currency.id, **kwargs
            ),  # Pass the payment context to allow overriding modules to check document access.
        }
        return request.render('bluemax_donations.website_donation_pay', rendering_context)

    @http.route('/website/donation/pay', type='http', methods=['GET', 'POST'], auth='public', website=True, sitemap=False)
    def website_donation_pay(self, **kwargs):
        kwargs['is_website_donation'] = True
        kwargs['currency_id'] = self._cast_as_int(kwargs.get('currency_id')) or request.env.company.currency_id.id
        kwargs['amount'] = self._cast_as_float(kwargs.get('amount')) or 5.0
        kwargs['donation_options'] = kwargs.get('donation_options', json_safe.dumps(dict(customAmount="freeAmount")))

        if request.env.user._is_public():
            kwargs['partner_id'] = request.env.user.partner_id.id
            kwargs['access_token'] = payment_utils.generate_access_token(kwargs['partner_id'], kwargs['amount'], kwargs['currency_id'])

        return self.website_payment_pay(**kwargs)

    @http.route('/website/donation/transaction/<minimum_amount>', type='json', auth='public', website=True, sitemap=False)
    def website_donation_transaction(self, amount, currency_id, partner_id, access_token, minimum_amount=0, **kwargs):
        if float(amount) < float(minimum_amount):
            raise ValidationError(_('Donation amount must be at least %.2f.', float(minimum_amount)))
        use_public_partner = request.env.user._is_public() or not partner_id
        if use_public_partner:
            details = kwargs['partner_details']
            if not details.get('name'):
                raise ValidationError(_('Name is required.'))
            partner_id = request.website.user_id.partner_id.id
            del kwargs['partner_details']
        else:
            partner_id = request.env.user.partner_id.id

        self._validate_transaction_kwargs(kwargs, additional_allowed_keys=(
            'partner_details', 'reference_prefix'
        ))
        if use_public_partner:
            kwargs['custom_create_values'] = {'tokenize': False}
        tx_sudo = self._create_transaction(
            amount=amount, currency_id=currency_id, partner_id=partner_id, **kwargs
        )
        tx_sudo.donation_payment = True
        if use_public_partner:
            tx_sudo.update({
                'partner_name': details['name'],
            })
        # the user can change the donation amount on the payment page,
        # therefor we need to recompute the access_token
        access_token = payment_utils.generate_access_token(
            tx_sudo.partner_id.id, tx_sudo.amount, tx_sudo.currency_id.id
        )
        self._update_landing_route(tx_sudo, access_token)

        # Send a notification to warn that a donation has been made
        # recipient_email = kwargs['donation_recipient_email']
        # comment = kwargs['donation_comment']
        # tx_sudo._send_donation_email(True, comment, recipient_email)

        return tx_sudo._get_processing_values()

    def _get_custom_extra_payment_form_values(
        self, donation_options=None, is_website_donation=False, **kwargs
    ):
        rendering_context = {}
        if is_website_donation:
            user_sudo = request.env.user
            logged_in = not user_sudo._is_public()
            partner_sudo = user_sudo.partner_id
            partner_details = {}
            if logged_in:
                partner_details = {
                    'name': partner_sudo.name,
                }

            countries = request.env['res.country'].sudo().search([])

            donation_options = json_safe.loads(donation_options) if donation_options else {}
            # donation_amounts = json_safe.loads(donation_options.get('donationAmounts', '[]'))
            donation_amounts = request.env['donation.amount'].sudo().search([]).mapped('amount')

            rendering_context.update({
                'is_website_donation': True,
                'partner': partner_sudo,
                'submit_button_label': _("Donate"),
                'transaction_route': '/website/donation/transaction/%s' % donation_options.get('minimumAmount', 0),
                'partner_details': partner_details,
                'error': {},
                'countries': countries,
                'donation_options': donation_options,
                'donation_amounts': donation_amounts,
            })
        return rendering_context
