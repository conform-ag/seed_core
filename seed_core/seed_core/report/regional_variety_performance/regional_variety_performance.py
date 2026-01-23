# Copyright (c) 2026, aremtech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart_data(data)
	return columns, data, None, chart


def get_columns(filters):
	columns = [
		{
			"label": _("Segment"),
			"fieldname": "segment",
			"fieldtype": "Link",
			"options": "Seed Segment",
			"width": 180
		},
		{
			"label": _("SubSegment"),
			"fieldname": "subsegment",
			"fieldtype": "Link",
			"options": "Seed SubSegment",
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
			"label": _("Lifecycle Stage"),
			"fieldname": "lifecycle_stage",
			"fieldtype": "Data",
			"width": 100
		}
	]

	if filters.get("territory"):
		columns.append({
			"label": _("Territory"),
			"fieldname": "territory",
			"fieldtype": "Link",
			"options": "Territory",
			"width": 120
		})

	columns.extend([
		{
			"label": _("Qty Sold"),
			"fieldname": "qty_sold",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"label": _("Avg Price"),
			"fieldname": "avg_price",
			"fieldtype": "Currency",
			"width": 100
		}
	])

	return columns


def get_data(filters):
	conditions = get_conditions(filters)

	group_by = "sv.seed_segment, sv.seed_subsegment, sv.name"
	if filters.get("territory"):
		group_by = "si.territory, " + group_by

	data = frappe.db.sql("""
		SELECT
			sv.seed_segment as segment,
			sv.seed_subsegment as subsegment,
			sv.name as variety,
			sv.lifecycle_stage,
			{territory_field}
			SUM(sii.qty) as qty_sold,
			SUM(sii.amount) as total_amount,
			CASE WHEN SUM(sii.qty) > 0 THEN SUM(sii.amount) / SUM(sii.qty) ELSE 0 END as avg_price
		FROM `tabSales Invoice Item` sii
		JOIN `tabSales Invoice` si ON sii.parent = si.name
		JOIN `tabItem` i ON sii.item_code = i.name
		LEFT JOIN `tabSeed Variety` sv ON sv.linked_item = i.name
		WHERE si.docstatus = 1
		AND sv.name IS NOT NULL
		{conditions}
		GROUP BY {group_by}
		ORDER BY total_amount DESC
	""".format(
		conditions=conditions,
		group_by=group_by,
		territory_field="si.territory as territory," if filters.get("territory") else ""
	), filters, as_dict=True)

	return data


def get_conditions(filters):
	conditions = ""

	if filters.get("company"):
		conditions += " AND si.company = %(company)s"

	if filters.get("fiscal_year"):
		fy = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
		conditions += f" AND si.posting_date BETWEEN '{fy.year_start_date}' AND '{fy.year_end_date}'"

	if filters.get("territory"):
		conditions += " AND si.territory = %(territory)s"

	if filters.get("crop"):
		conditions += " AND sv.seed_crop = %(crop)s"

	if filters.get("segment"):
		conditions += " AND sv.seed_segment = %(segment)s"

	if filters.get("lifecycle_stage"):
		conditions += " AND sv.lifecycle_stage = %(lifecycle_stage)s"

	return conditions


def get_chart_data(data):
	if not data:
		return None

	# Get top 10 varieties by amount
	top_data = sorted(data, key=lambda x: flt(x.get("total_amount", 0)), reverse=True)[:10]

	labels = [d.get("variety", "Unknown") for d in top_data]
	values = [flt(d.get("total_amount", 0)) for d in top_data]

	return {
		"data": {
			"labels": labels,
			"datasets": [{"name": _("Sales Amount"), "values": values}]
		},
		"type": "bar",
		"colors": ["#7cd6fd"]
	}
