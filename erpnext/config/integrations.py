from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Payments"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "GoCardless Settings",
					"description": _("GoCardless payment gateway settings"),
				},
				{
					"type": "doctype",
					"name": "GoCardless Mandate",
					"description": _("GoCardless SEPA Mandate"),
				}
			]
		},
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "Woocommerce Settings"
				},
				{
					"type": "doctype",
					"name": "Shopify Settings",
					"description": _("Connect Shopify with OneHash"),
				},
				{
					"type": "doctype",
					"name": "Amazon MWS Settings",
					"description": _("Connect Amazon with OneHash"),
				},
				{
					"type": "doctype",
					"name": "Plaid Settings",
					"description": _("Connect your bank accounts to OneHash"),
				},
				{
					"type": "doctype",
					"name": "Exotel Settings",
					"description": _("Connect your Exotel Account to OneHash and track call logs"),
				}
			]
		}
	]
