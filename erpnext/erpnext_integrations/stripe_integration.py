# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, ast
from frappe import _
from frappe.utils import cint, flt
from frappe.integrations.utils import create_request_log
import stripe
from stripe.api_resources import balance_transaction

def create_stripe_charge(gateway_controller, data):
	stripe_settings = frappe.get_doc("Stripe Settings", gateway_controller)
	stripe_settings.data = frappe._dict(data)
	
	try:
		stripe_settings.data.amount = cint(flt(stripe_settings.data.amount)*100)
		stripe.api_key = stripe_settings.get_password(fieldname="secret_key", raise_exception=False)
		stripe.default_http_client = stripe.http_client.RequestsClient()

		stripe_settings.integration_request = create_request_log(stripe_settings.data, "Host", "Stripe")
		return create_charge_on_stripe(stripe_settings)
	except:
		frappe.log_error(frappe.get_traceback(), "Stripe Charge Error")

def create_charge_on_stripe(stripe_settings):
	try:
		charge = stripe.Charge.create(
			amount= stripe_settings.data.amount,
			currency= stripe_settings.data.currency,
			source= stripe_settings.data.stripe_token_id,
			description= stripe_settings.data.description,
			receipt_email= stripe_settings.data.payer_email,
			metadata= ast.literal_eval(stripe_settings.data.metadata)
			)
		if charge.captured == True:
			stripe_settings.integration_request.db_set('status', 'Completed', update_modified=False)
			stripe_settings.flags.status_changed_to = "Completed"

		else:
			stripe_settings.integration_request.db_set('status', 'Failed', update_modified=False)
			frappe.log_error(charge.failure_message, 'Stripe Payment not completed')

	except Exception:
		stripe_settings.integration_request.db_set('status', 'Failed', update_modified=False)
		frappe.log_error(frappe.get_traceback())

	return stripe_settings.finalize_request()

def create_stripe_refund(gateway_controller,data):
	stripe_settings = frappe.get_doc("Stripe Settings", gateway_controller)
	stripe_settings.data = frappe._dict(data)

	stripe.api_key = stripe_settings.get_password(fieldname="secret_key", raise_exception=False)
	stripe.default_http_client = stripe.http_client.RequestsClient()

	try:
		balance_transaction = stripe.Customer.create_balance_transaction(stripe_settings.data.customer,amount=stripe_settings.data.amount,currency=stripe_settings.data.currency)
		stripe_settings.data.balance_transaction = balance_transaction.get("id",None)
		return create_refund_on_stripe(stripe_settings)

	except Exception:
		frappe.log_error(frappe.get_traceback())


def retrieve_stripe_invoice(gateway_controller,data):
	stripe_settings = frappe.get_doc("Stripe Settings", gateway_controller)
	stripe_settings.data = frappe._dict(data)

	stripe.api_key = stripe_settings.get_password(fieldname="secret_key", raise_exception=False)
	stripe.default_http_client = stripe.http_client.RequestsClient()

	try:
		invoice = stripe.Invoice.retrieve(stripe_settings.data.invoice_id)
		return invoice
	except Exception:
		frappe.log_error(frappe.get_traceback())


def create_refund_on_stripe(stripe_settings):
	try:
		return stripe.Refund.create(
			amount= stripe_settings.data.amount,
			source= stripe_settings.data.stripe_token_id,
			description= stripe_settings.data.description,
			receipt_email= stripe_settings.data.payer_email,
			charge = stripe_settings.data.charge_id
			)
		
	except Exception:
		frappe.log_error(frappe.get_traceback())





def create_stripe_subscription(gateway_controller, data):
	stripe_settings = frappe.get_doc("Stripe Settings", gateway_controller)
	stripe_settings.data = frappe._dict(data)

	stripe.api_key = stripe_settings.get_password(fieldname="secret_key", raise_exception=False)
	stripe.default_http_client = stripe.http_client.RequestsClient()

	try:
		stripe_settings.integration_request = create_request_log(stripe_settings.data, "Host", "Stripe")
		
		# For Stripe Subscription Model
		if not stripe_settings.data.reference_doctype == "Saas Site":
			# Core Function
			stripe_settings.payment_plans = frappe.get_doc("Payment Request", stripe_settings.data.reference_docname).subscription_plans
		
		return create_subscription_on_stripe(stripe_settings)

	except Exception:
		frappe.log_error(frappe.get_traceback())
		return{
			"redirect_to": frappe.redirect_to_message(_('Server Error'), _("It seems that there is an issue with the server's stripe configuration. In case of failure, the amount will get refunded to your account.")),
			"status": 401
		}


def create_subscription_on_stripe(stripe_settings):
		items = []
		if stripe_settings.data.reference_doctype == "Saas Site":
			# For Stripe Subscription Model
			items.append({"plan": stripe_settings.data.plan_id, "quantity": stripe_settings.data.quantity})
			metadata={'site_name': stripe_settings.data.reference_docname}
		
		else:
			# Core Function
			for payment_plan in stripe_settings.payment_plans:
				plan = frappe.db.get_value("Subscription Plan", payment_plan.plan, "payment_plan_id")
				items.append({"plan": plan, "quantity": payment_plan.qty})
				metadata={}

		try:
			customer = stripe.Customer.create(description=stripe_settings.data.payer_name, name=stripe_settings.data.payer_name, email=stripe_settings.data.payer_email, source=stripe_settings.data.stripe_token_id)
			subscription = stripe.Subscription.create(customer=customer, items=items, metadata=metadata)

			if subscription.status == "active":
				stripe_settings.integration_request.db_set('status', 'Completed', update_modified=False)
				stripe_settings.flags.status_changed_to = "Completed"

			else:
				stripe_settings.integration_request.db_set('status', 'Failed', update_modified=False)
				frappe.log_error('Subscription No: ' + subscription.id, 'Stripe Payment not completed')

		except Exception:
			stripe_settings.integration_request.db_set('status', 'Failed', update_modified=False)
			frappe.log_error(frappe.get_traceback())

		return stripe_settings.finalize_request()


def stripe_update_subscription(gateway_controller, data):
	stripe_settings = frappe.get_doc("Stripe Settings", gateway_controller)
	stripe_settings.data = frappe._dict(data)

	stripe.api_key = stripe_settings.get_password(fieldname="secret_key", raise_exception=False)
	stripe.default_http_client = stripe.http_client.RequestsClient()

	try:
		stripe_settings.integration_request = create_request_log(stripe_settings.data, "Host", "Stripe")
		return update_subscription_on_stripe(stripe_settings)
	except Exception:
		frappe.log_error(frappe.get_traceback())
		return{
			"redirect_to": frappe.redirect_to_message(_('Server Error'), _("It seems that there is an issue with the server's stripe configuration. In case of failure, the amount will get refunded to your account.")),
			"status": 401
		}


def update_subscription_on_stripe(stripe_settings):
	# For Stripe Subscription Model
	
	subscription_id = stripe_settings.data.subscription_id
	
	items = []
	items.append({"id": stripe_settings.data.subscription_item_id, "quantity": stripe_settings.data.quantity})
	metadata={'site_name': stripe_settings.data.site_name}

	try:
		subscription = stripe.Subscription.modify(subscription_id, cancel_at_period_end=False, items=items, metadata=metadata,billing_cycle_anchor='now',proration_behavior='create_prorations') # Will create invoice immediately along with proration adjustments.

		if subscription.status == "active":
			stripe_settings.integration_request.db_set('status', 'Completed', update_modified=False)
			stripe_settings.flags.status_changed_to = "Completed"

		else:
			stripe_settings.integration_request.db_set('status', 'Failed', update_modified=False)
			frappe.log_error('Subscription No: ' + subscription.id, 'Stripe Payment not completed')

	except Exception:
		stripe_settings.integration_request.db_set('status', 'Failed', update_modified=False)
		frappe.log_error(frappe.get_traceback())

	return stripe_settings.finalize_request()

def stripe_cancel_subscription(gateway_controller, data):
	stripe_settings = frappe.get_doc("Stripe Settings", gateway_controller)
	stripe_settings.data = frappe._dict(data)

	stripe.api_key = stripe_settings.get_password(fieldname="secret_key", raise_exception=False)
	stripe.default_http_client = stripe.http_client.RequestsClient()

	try:
		stripe_settings.integration_request = create_request_log(stripe_settings.data, "Host", "Stripe")
		return cancel_subscription_on_stripe(stripe_settings)
	except Exception:
		frappe.log_error(frappe.get_traceback())
		return{
			"redirect_to": frappe.redirect_to_message(_('Server Error'), _("It seems that there is an issue with the server's stripe configuration. In case of failure, the amount will get refunded to your account.")),
			"status": 401
		}


def cancel_subscription_on_stripe(stripe_settings):
	# For Stripe Subscription Model
	
	subscription_id = stripe_settings.data.subscription_id

	try:
		subscription = stripe.Subscription.modify(subscription_id, cancel_at_period_end= True)

		if subscription.cancel_at_period_end == "true":
			stripe_settings.integration_request.db_set('status', 'Cancelled', update_modified=False)
			stripe_settings.flags.status_changed_to = "Cancelled"

	except Exception:
		stripe_settings.integration_request.db_set('status', 'Failed', update_modified=False)
		frappe.log_error(frappe.get_traceback(),"Cancel Stripe Subscription")

	return stripe_settings.finalize_request()