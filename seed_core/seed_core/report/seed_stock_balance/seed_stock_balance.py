# Copyright (c) 2026, aremtech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, today


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"label": _("Crop"),
			"fieldname": "crop",
			"fieldtype": "Link",
			"options": "Seed Crop",
			"width": 120
		},
		{
			"label": _("Segment"),
			"fieldname": "segment",
			"fieldtype": "Link",
			"options": "Seed Segment",
			"width": 150
		},
		{
			"label": _("Variety"),
			"fieldname": "variety",
			"fieldtype": "Link",
			"options": "Seed Variety",
			"width": 150
		},
		{
			"label": _("Batch"),
			"fieldname": "batch",
			"fieldtype": "Link",
			"options": "Batch",
			"width": 120
		},
		{
			"label": _("Warehouse"),
			"fieldname": "warehouse",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 150
		},
		{
			"label": _("Qty"),
			"fieldname": "qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Germination %"),
			"fieldname": "germination_percent",
			"fieldtype": "Percent",
			"width": 110
		},
		{
			"label": _("Purity %"),
			"fieldname": "purity_percent",
			"fieldtype": "Percent",
			"width": 90
		},
		{
			"label": _("Test Date"),
			"fieldname": "lab_test_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Retest Date"),
			"fieldname": "next_retest_date",
			"fieldtype": "Date",
			"width": 100
		},
		{
			"label": _("Organic"),
			"fieldname": "is_organic",
			"fieldtype": "Check",
			"width": 70
		},
		{
			"label": _("Treated"),
			"fieldname": "is_treated",
			"fieldtype": "Check",
			"width": 70
		},
		{
			"label": _("Status"),
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 100
		}
	]


def get_data(filters):
	conditions = get_conditions(filters)

	# Get stock ledger entries grouped by batch and warehouse
	data = frappe.db.sql("""
		SELECT
			sv.seed_crop as crop,
			sv.seed_segment as segment,
			sv.name as variety,
			b.name as batch,
			sle.warehouse,
			SUM(sle.actual_qty) as qty,
			b.germination_percent,
			b.purity_percent,
			b.lab_test_date,
			b.next_retest_date,
			b.is_organic,
			CASE WHEN b.is_chemically_treated = 1 OR b.is_pelleted = 1 OR b.is_primed = 1 OR b.is_coated = 1 THEN 1 ELSE 0 END as is_treated
		FROM `tabStock Ledger Entry` sle
		JOIN `tabBatch` b ON sle.batch_no = b.name
		JOIN `tabItem` i ON sle.item_code = i.name
		LEFT JOIN `tabSeed Variety` sv ON sv.linked_item = i.name
		WHERE sle.is_cancelled = 0
		{conditions}
		GROUP BY sle.batch_no, sle.warehouse
		HAVING SUM(sle.actual_qty) > 0
		ORDER BY sv.seed_crop, sv.seed_segment, sv.name, b.name, sle.warehouse
	""".format(conditions=conditions), filters, as_dict=True)

	# Add status based on retest date
	today_date = getdate(today())
	for row in data:
		if row.next_retest_date:
			if getdate(row.next_retest_date) < today_date:
				row["status"] = "Retest Due"
			elif (getdate(row.next_retest_date) - today_date).days <= 30:
				row["status"] = "Retest Soon"
			else:
				row["status"] = "OK"
		else:
			row["status"] = "No Test"

	return data


def get_conditions(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " AND sle.company = %(company)s"

	if filters.get("warehouse"):
		conditions += " AND sle.warehouse = %(warehouse)s"

	if filters.get("crop"):
		conditions += " AND sv.seed_crop = %(crop)s"

	if filters.get("segment"):
		conditions += " AND sv.seed_segment = %(segment)s"

	if filters.get("variety"):
		conditions += " AND sv.name = %(variety)s"

	if filters.get("show_organic_only"):
		conditions += " AND b.is_organic = 1"

	if filters.get("show_untreated_only"):
		conditions += " AND b.is_chemically_treated = 0 AND b.is_pelleted = 0 AND b.is_primed = 0 AND b.is_coated = 0"

	if filters.get("show_retest_due"):
		conditions += f" AND b.next_retest_date < '{today()}'"

	return conditions
