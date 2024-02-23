{
    "name": "Donation Payments",
    "version": "1.0",
    "category": "eCommerce",
    'sequence': 1,
    'author': 'BlueMax Pay',
    "summary": "BlueMax Pay Implementation:- Donation Payments Module allows user to donate money of specific amount set by administrator and supports various payment acquirers for the same | Donation | Donation amount | Donation Payment | Donation Stripe | Donation Master Card | Donation Wire Transfer |",
    'description': """
BlueMax Pay
Donation Payments
====================
=> Donate money from website
=> Donation from various payment acquirers supported
    """,
    'depends': ['website', 'account_payment', 'portal'],
    "data": [
        'security/ir.model.access.csv',
        'data/donation_amount_data.xml',
        'views/donation_amount_views.xml',
        'views/donation_amount_templates.xml',
        'views/snippets.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'bluemax_donations/static/src/js/website_donation.js',
            'bluemax_donations/static/src/js/payment_form.js',
            'bluemax_donations/static/src/js/website_payment_donation.js',
            'bluemax_donations/static/src/css/donation_payment.css',
        ],
    },
    "application": True,
    'license': 'LGPL-3',
}
