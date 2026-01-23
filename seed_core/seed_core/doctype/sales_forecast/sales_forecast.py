# Copyright (c) 2026, aremtech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SalesForecast(Document):
	def validate(self):
		self.calculate_expected_amounts()
		self.calculate_totals()

	def calculate_expected_amounts(self):
		"""Calculate expected amount for each forecast item."""
		for item in self.forecast_items:
			item.expected_amount = flt(item.suggested_qty) * flt(item.suggested_price)

	def calculate_totals(self):
		"""Calculate total forecast values."""
		self.total_suggested_qty = sum(flt(d.suggested_qty) for d in self.forecast_items)
		self.total_expected_amount = sum(flt(d.expected_amount) for d in self.forecast_items)

	@frappe.whitelist()
	def fetch_last_year_actuals(self):
		"""Fetch last year's actual sales for each variety."""
		if not self.fiscal_year or not self.customer:
			frappe.throw(_("Please set Fiscal Year and Customer first"))

		# Get previous fiscal year
		current_fy = frappe.get_doc("Fiscal Year", self.fiscal_year)
		prev_fy = frappe.db.get_value(
			"Fiscal Year",
			{"year_end_date": ["<", current_fy.year_start_date]},
			"name",
			order_by="year_end_date desc"
		)

		if not prev_fy:
			frappe.msgprint(_("No previous fiscal year found"))
			return

		prev_fy_doc = frappe.get_doc("Fiscal Year", prev_fy)

		for item in self.forecast_items:
			if not item.seed_variety:
				continue

			# Get linked Item
			linked_item = frappe.db.get_value("Seed Variety", item.seed_variety, "linked_item")
			if not linked_item:
				continue

			# Query last year's actuals
			actuals = frappe.db.sql("""
				SELECT SUM(sii.qty) as qty, SUM(sii.amount) as amount
				FROM `tabSales Invoice Item` sii
				JOIN `tabSales Invoice` si ON sii.parent = si.name
				WHERE si.docstatus = 1
				AND si.customer = %(customer)s
				AND sii.item_code = %(item_code)s
				AND si.posting_date BETWEEN %(start_date)s AND %(end_date)s
			""", {
				"customer": self.customer,
				"item_code": linked_item,
				"start_date": prev_fy_doc.year_start_date,
				"end_date": prev_fy_doc.year_end_date
			}, as_dict=True)

			if actuals and actuals[0]:
				item.last_year_qty = flt(actuals[0].qty)
				item.last_year_amount = flt(actuals[0].amount)

		self.save()
		frappe.msgprint(_("Last year actuals fetched from {0}").format(prev_fy))
