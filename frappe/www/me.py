# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# MIT License. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
import frappe.www.list

from erpnext.controllers.website_list_for_contact import get_customers_suppliers

no_cache = 1

def get_context(context):
	if frappe.session.user=='Guest':
		frappe.throw(_("You need to be logged in to access this page"), frappe.PermissionError)

	context.supplier = None
	context.customer = None

	customers, suppliers = get_customers_suppliers('Supplier', frappe.session.user)

	if suppliers:
		context.supplier = suppliers[0]

	if customers:
		context.customer = customers[0]


	context.show_sidebar=True