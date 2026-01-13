"""
Consolidated Sales Dashboard Report
Shows sales performance across parent and subsidiaries with KPIs, charts, and detailed breakdown
"""
import frappe
from frappe import _
from frappe.utils import flt, getdate, now_datetime


def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data, filters)
    report_summary = get_report_summary(data, filters)
    
    return columns, data, None, chart, report_summary


def get_columns(filters):
    columns = [
        {
            "fieldname": "dimension",
            "label": _("Dimension"),
            "fieldtype": "Data",
            "width": 180
        },
        {
            "fieldname": "target_qty",
            "label": _("Target Qty"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "actual_qty",
            "label": _("Actual Qty"),
            "fieldtype": "Float",
            "width": 100
        },
        {
            "fieldname": "target_amount",
            "label": _("Target Amt"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "actual_amount",
            "label": _("Actual Amt"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "variance_qty",
            "label": _("Var Qty"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "variance_pct",
            "label": _("Var %"),
            "fieldtype": "Percent",
            "width": 80
        },
        {
            "fieldname": "achievement_pct",
            "label": _("Achievement %"),
            "fieldtype": "Percent",
            "width": 100
        }
    ]
    
    if filters.get("scope") != "Local Only":
        columns.insert(1, {
            "fieldname": "source",
            "label": _("Source"),
            "fieldtype": "Data",
            "width": 100
        })
    
    return columns


def get_data(filters):
    data = []
    
    # Get fiscal year dates
    fy = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
    
    # Determine view type based on report context
    # For now, aggregate by Crop
    
    # Get local targets
    local_targets = get_local_targets(filters, fy)
    
    # Get local actuals
    local_actuals = get_local_actuals(filters, fy)
    
    # Merge local data
    local_data = merge_targets_actuals(local_targets, local_actuals, "Local")
    data.extend(local_data)
    
    # Get subsidiary data if requested
    if filters.get("scope") in ["Include Subsidiaries", "Subsidiaries Only"]:
        subsidiary_data = get_subsidiary_data(filters, fy)
        data.extend(subsidiary_data)
    
    # Sort by source and dimension
    data.sort(key=lambda x: (x.get("source", ""), x.get("dimension", "")))
    
    return data


def get_local_targets(filters, fy):
    """Get targets from local Sales Target Plans"""
    conditions = ["stp.docstatus = 1", "stp.fiscal_year = %(fiscal_year)s"]
    
    if filters.get("company"):
        conditions.append("stp.company = %(company)s")
    
    if filters.get("territory"):
        conditions.append("stp.target_level = 'Territory' AND stp.party = %(territory)s")
    
    query = f"""
        SELECT 
            sti.crop as dimension,
            SUM(sti.forecast_qty) as target_qty,
            SUM(sti.forecast_amount) as target_amount
        FROM `tabSales Target Plan` stp
        JOIN `tabSales Target Item` sti ON sti.parent = stp.name
        WHERE {' AND '.join(conditions)}
        GROUP BY sti.crop
    """
    
    results = frappe.db.sql(query, filters, as_dict=True)
    return {row.dimension: row for row in results if row.dimension}


def get_local_actuals(filters, fy):
    """Get actuals from local Sales Invoices"""
    conditions = ["si.docstatus = 1"]
    conditions.append("si.posting_date BETWEEN %(start_date)s AND %(end_date)s")
    
    if filters.get("company"):
        conditions.append("si.company = %(company)s")
    
    if filters.get("territory"):
        conditions.append("si.territory = %(territory)s")
    
    params = dict(filters)
    params["start_date"] = fy.year_start_date
    params["end_date"] = fy.year_end_date
    
    # Join with Seed Variety to get crop
    query = f"""
        SELECT 
            sv.crop as dimension,
            SUM(sii.qty) as actual_qty,
            SUM(sii.amount) as actual_amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        LEFT JOIN `tabSeed Variety` sv ON sv.name = sii.item_code
        WHERE {' AND '.join(conditions)}
        GROUP BY sv.crop
    """
    
    results = frappe.db.sql(query, params, as_dict=True)
    return {row.dimension: row for row in results if row.dimension}


def get_subsidiary_data(filters, fy):
    """Get data from Subsidiary Sales Summary"""
    conditions = ["fiscal_year = %(fiscal_year)s"]
    
    if filters.get("subsidiary"):
        if filters.get("subsidiary") != "All Subsidiaries":
            sub_code = filters.get("subsidiary").split(" - ")[0]
            conditions.append(f"subsidiary_code = '{sub_code}'")
    
    if filters.get("crop"):
        conditions.append("crop = %(crop)s")
    
    query = f"""
        SELECT 
            subsidiary_code as source,
            crop as dimension,
            SUM(qty) as actual_qty,
            SUM(amount) as actual_amount
        FROM `tabSubsidiary Sales Summary`
        WHERE {' AND '.join(conditions)}
        GROUP BY subsidiary_code, crop
    """
    
    results = frappe.db.sql(query, filters, as_dict=True)
    
    data = []
    for row in results:
        data.append({
            "dimension": row.dimension or "Unknown",
            "source": get_subsidiary_name(row.source),
            "target_qty": 0,  # Targets are on parent
            "target_amount": 0,
            "actual_qty": flt(row.actual_qty),
            "actual_amount": flt(row.actual_amount),
            "variance_qty": flt(row.actual_qty),
            "variance_pct": 0,
            "achievement_pct": 0
        })
    
    return data


def merge_targets_actuals(targets, actuals, source):
    """Merge target and actual data"""
    data = []
    
    all_dimensions = set(targets.keys()) | set(actuals.keys())
    
    for dimension in all_dimensions:
        target = targets.get(dimension, {})
        actual = actuals.get(dimension, {})
        
        target_qty = flt(target.get("target_qty", 0))
        target_amount = flt(target.get("target_amount", 0))
        actual_qty = flt(actual.get("actual_qty", 0))
        actual_amount = flt(actual.get("actual_amount", 0))
        
        variance_qty = actual_qty - target_qty
        variance_pct = (variance_qty / target_qty * 100) if target_qty else 0
        achievement_pct = (actual_qty / target_qty * 100) if target_qty else 0
        
        data.append({
            "dimension": dimension,
            "source": source,
            "target_qty": target_qty,
            "target_amount": target_amount,
            "actual_qty": actual_qty,
            "actual_amount": actual_amount,
            "variance_qty": variance_qty,
            "variance_pct": variance_pct,
            "achievement_pct": achievement_pct
        })
    
    return data


def get_subsidiary_name(code):
    """Map subsidiary code to name"""
    mapping = {
        "MA": "Morocco",
        "ES": "Spain",
        "TR": "Turkey"
    }
    return mapping.get(code, code)


def get_chart(data, filters):
    if not data:
        return None
    
    # Group by dimension for chart
    dimensions = {}
    for row in data:
        dim = row.get("dimension")
        if dim not in dimensions:
            dimensions[dim] = {"target": 0, "actual": 0}
        dimensions[dim]["target"] += flt(row.get("target_qty"))
        dimensions[dim]["actual"] += flt(row.get("actual_qty"))
    
    labels = list(dimensions.keys())
    target_values = [dimensions[d]["target"] for d in labels]
    actual_values = [dimensions[d]["actual"] for d in labels]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Target Qty",
                    "values": target_values,
                    "chartType": "bar"
                },
                {
                    "name": "Actual Qty",
                    "values": actual_values,
                    "chartType": "bar"
                }
            ]
        },
        "type": "bar",
        "colors": ["#2490ef", "#28a745"]
    }


def get_report_summary(data, filters):
    if not data:
        return []
    
    total_target_qty = sum(flt(row.get("target_qty")) for row in data)
    total_actual_qty = sum(flt(row.get("actual_qty")) for row in data)
    total_target_amt = sum(flt(row.get("target_amount")) for row in data)
    total_actual_amt = sum(flt(row.get("actual_amount")) for row in data)
    
    achievement = (total_actual_qty / total_target_qty * 100) if total_target_qty else 0
    
    summary = [
        {
            "value": total_target_qty,
            "label": "Total Target Qty",
            "datatype": "Float"
        },
        {
            "value": total_actual_qty,
            "label": "Total Actual Qty",
            "datatype": "Float"
        },
        {
            "value": total_actual_amt,
            "label": "Total Revenue",
            "datatype": "Currency"
        },
        {
            "value": achievement,
            "label": "Achievement %",
            "datatype": "Percent",
            "indicator": "Green" if achievement >= 100 else ("Red" if achievement < 80 else "Orange")
        }
    ]
    
    return summary
