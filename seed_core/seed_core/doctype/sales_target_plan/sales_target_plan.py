# Copyright (c) 2026, aremtech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SalesTargetPlan(Document):
	def validate(self):
		self.calculate_totals()

	def calculate_totals(self):
		"""Calculate total targets from child table."""
		self.total_target_qty = sum(flt(d.target_qty) for d in self.target_items)
		self.total_target_amount = sum(flt(d.target_amount) for d in self.target_items)
		self.total_actual_qty = sum(flt(d.actual_qty) for d in self.target_items)
		self.total_actual_amount = sum(flt(d.actual_amount) for d in self.target_items)

		if self.total_target_amount:
			self.achievement_percent = (self.total_actual_amount / self.total_target_amount) * 100
		else:
			self.achievement_percent = 0

	def on_submit(self):
		self.db_set("status", "Draft")

	@frappe.whitelist()
	def calculate_actuals(self):
		"""Calculate actual sales from Sales Invoices."""
		if not self.fiscal_year:
			frappe.throw(_("Please set Fiscal Year"))

		# Get fiscal year dates
		fy = frappe.get_doc("Fiscal Year", self.fiscal_year)

		for item in self.target_items:
			if not item.seed_variety:
				continue

			# Get linked Item from Seed Variety
			linked_item = frappe.db.get_value("Seed Variety", item.seed_variety, "linked_item")
			if not linked_item:
				continue

			# Build query filters
			filters = {
				"docstatus": 1,
				"posting_date": ["between", [fy.year_start_date, fy.year_end_date]],
				"item_code": linked_item
			}

			# Add entity-specific filter
			if self.target_for == "Customer" and self.target_entity:
				filters["customer"] = self.target_entity
			elif self.target_for == "Territory" and self.target_entity:
				filters["territory"] = self.target_entity

			# Add month filter if specified
			if item.month:
				month_num = self.get_month_number(item.month)
				if month_num:
					filters["posting_date"] = ["between", [
						f"{fy.year_start_date.year if month_num >= fy.year_start_date.month else fy.year_end_date.year}-{month_num:02d}-01",
						f"{fy.year_start_date.year if month_num >= fy.year_start_date.month else fy.year_end_date.year}-{month_num:02d}-31"
					]]

			# Query Sales Invoice Items
			actuals = frappe.db.sql("""
				SELECT SUM(sii.qty) as qty, SUM(sii.amount) as amount
				FROM `tabSales Invoice Item` sii
				JOIN `tabSales Invoice` si ON sii.parent = si.name
				WHERE si.docstatus = 1
				AND sii.item_code = %(item_code)s
				AND si.posting_date BETWEEN %(start_date)s AND %(end_date)s
			""", {
				"item_code": linked_item,
				"start_date": fy.year_start_date,
				"end_date": fy.year_end_date
			}, as_dict=True)

			if actuals and actuals[0]:
				item.actual_qty = flt(actuals[0].qty)
				item.actual_amount = flt(actuals[0].amount)

		self.calculate_totals()
		self.save()
		frappe.msgprint(_("Actuals calculated from Sales Invoices"))

	def get_month_number(self, month_name):
		"""Convert month name to number."""
		months = {
			"January": 1, "February": 2, "March": 3, "April": 4,
			"May": 5, "June": 6, "July": 7, "August": 8,
			"September": 9, "October": 10, "November": 11, "December": 12
		}
		return months.get(month_name)

	@frappe.whitelist()
	def consolidate_forecasts(self, forecast_names):
		"""Consolidate multiple Sales Forecasts into this target plan."""
		if isinstance(forecast_names, str):
			forecast_names = frappe.parse_json(forecast_names)

		for forecast_name in forecast_names:
			forecast = frappe.get_doc("Sales Forecast", forecast_name)

			for f_item in forecast.forecast_items:
				# Check if variety already exists in targets
				existing = next(
					(t for t in self.target_items if t.seed_variety == f_item.seed_variety),
					None
				)

				if existing:
					# Sum quantities
					existing.target_qty = flt(existing.target_qty) + flt(f_item.suggested_qty)
					existing.target_amount = flt(existing.target_amount) + flt(f_item.expected_amount)
				else:
					# Add new target item
					self.append("target_items", {
						"seed_variety": f_item.seed_variety,
						"target_qty": f_item.suggested_qty,
						"target_amount": f_item.expected_amount
					})

		self.calculate_totals()
		self.save()
		frappe.msgprint(_("Consolidated {0} forecasts").format(len(forecast_names)))
