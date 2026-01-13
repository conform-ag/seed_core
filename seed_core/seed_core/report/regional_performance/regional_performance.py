"""
Regional Performance Report
Shows sales performance by territory/region with manager attribution
"""
import frappe
from frappe import _
from frappe.utils import flt


def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    chart = get_chart(data)
    report_summary = get_report_summary(data)
    
    return columns, data, None, chart, report_summary


def get_columns():
    return [
        {
            "fieldname": "territory",
            "label": _("Territory"),
            "fieldtype": "Link",
            "options": "Territory",
            "width": 150
        },
        {
            "fieldname": "region",
            "label": _("Region"),
            "fieldtype": "Data",
            "width": 120
        },
        {
            "fieldname": "manager",
            "label": _("Manager"),
            "fieldtype": "Data",
            "width": 120
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
            "fieldname": "achievement_pct",
            "label": _("Achievement %"),
            "fieldtype": "Percent",
            "width": 110
        },
        {
            "fieldname": "customers",
            "label": _("Customers"),
            "fieldtype": "Int",
            "width": 80
        },
        {
            "fieldname": "orders",
            "label": _("Orders"),
            "fieldtype": "Int",
            "width": 80
        }
    ]


def get_data(filters):
    fy = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
    
    # Get territories with their parent regions
    territories = get_territories(filters)
    
    data = []
    for territory in territories:
        # Get targets for this territory
        targets = get_territory_targets(territory.name, filters)
        
        # Get actuals for this territory
        actuals = get_territory_actuals(territory.name, filters, fy)
        
        target_qty = flt(targets.get("target_qty", 0))
        actual_qty = flt(actuals.get("actual_qty", 0))
        achievement = (actual_qty / target_qty * 100) if target_qty else 0
        
        data.append({
            "territory": territory.name,
            "region": get_region(territory),
            "manager": get_territory_manager(territory.name),
            "target_qty": target_qty,
            "actual_qty": actual_qty,
            "target_amount": flt(targets.get("target_amount", 0)),
            "actual_amount": flt(actuals.get("actual_amount", 0)),
            "achievement_pct": achievement,
            "customers": actuals.get("customers", 0),
            "orders": actuals.get("orders", 0)
        })
    
    # Sort by achievement descending
    data.sort(key=lambda x: x.get("achievement_pct", 0), reverse=True)
    
    return data


def get_territories(filters):
    """Get relevant territories"""
    conditions = []
    
    if filters.get("territory"):
        # Get this territory and its children
        territory = frappe.get_doc("Territory", filters.get("territory"))
        conditions.append(f"lft >= {territory.lft} AND rgt <= {territory.rgt}")
    
    if filters.get("region"):
        # Map region to parent territories
        region_map = {
            "Europe": ["Spain", "Netherlands", "Poland", "France"],
            "Maghreb/Africa": ["Morocco", "Algeria", "Tunisia"],
            "LATAM": ["Mexico", "Brazil", "Chile"],
            "USA/Canada": ["USA", "Canada"],
            "Asia": ["Turkey"]
        }
        territories = region_map.get(filters.get("region"), [])
        if territories:
            formatted = "', '".join(territories)
            conditions.append(f"name IN ('{formatted}')")
    
    where_clause = " AND ".join(conditions) if conditions else "is_group = 0"
    
    query = f"""
        SELECT name, lft, rgt, parent_territory
        FROM `tabTerritory`
        WHERE {where_clause}
        ORDER BY name
    """
    
    return frappe.db.sql(query, as_dict=True)


def get_region(territory):
    """Determine region from territory hierarchy"""
    region_mapping = {
        "Morocco": "Maghreb/Africa",
        "Spain": "Europe",
        "Netherlands": "Europe",
        "Poland": "Europe",
        "France": "Europe",
        "Mexico": "LATAM",
        "USA": "USA/Canada",
        "Turkey": "Asia"
    }
    return region_mapping.get(territory.name, territory.parent_territory or "")


def get_territory_manager(territory_name):
    """Get manager assigned to territory"""
    # Could be from a custom field or Sales Person assignment
    manager_mapping = {
        "Morocco": "Nassir",
        "Spain": "Nico",
        "Netherlands": "Nico",
        "Poland": "Oskar",
        "Mexico": "Miguel",
        "USA": "Hicham"
    }
    return manager_mapping.get(territory_name, "")


def get_territory_targets(territory, filters):
    """Get targets for a territory"""
    result = frappe.db.sql("""
        SELECT 
            SUM(sti.forecast_qty) as target_qty,
            SUM(sti.forecast_amount) as target_amount
        FROM `tabSales Target Plan` stp
        JOIN `tabSales Target Item` sti ON sti.parent = stp.name
        WHERE stp.docstatus = 1
            AND stp.fiscal_year = %(fiscal_year)s
            AND stp.party = %(territory)s
    """, {"fiscal_year": filters.get("fiscal_year"), "territory": territory}, as_dict=True)
    
    return result[0] if result else {}


def get_territory_actuals(territory, filters, fy):
    """Get actuals for a territory"""
    result = frappe.db.sql("""
        SELECT 
            SUM(sii.qty) as actual_qty,
            SUM(sii.amount) as actual_amount,
            COUNT(DISTINCT si.customer) as customers,
            COUNT(DISTINCT si.name) as orders
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1
            AND si.territory = %(territory)s
            AND si.posting_date BETWEEN %(start_date)s AND %(end_date)s
    """, {
        "territory": territory,
        "start_date": fy.year_start_date,
        "end_date": fy.year_end_date
    }, as_dict=True)
    
    return result[0] if result else {}


def get_chart(data):
    if not data:
        return None
    
    labels = [row.get("territory") for row in data[:10]]  # Top 10
    values = [row.get("achievement_pct") for row in data[:10]]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "Achievement %",
                    "values": values
                }
            ]
        },
        "type": "bar",
        "colors": ["#2490ef"]
    }


def get_report_summary(data):
    if not data:
        return []
    
    total_target = sum(flt(row.get("target_qty")) for row in data)
    total_actual = sum(flt(row.get("actual_qty")) for row in data)
    total_revenue = sum(flt(row.get("actual_amount")) for row in data)
    total_customers = sum(row.get("customers", 0) for row in data)
    
    overall_achievement = (total_actual / total_target * 100) if total_target else 0
    
    return [
        {
            "value": len(data),
            "label": "Territories",
            "datatype": "Int"
        },
        {
            "value": total_customers,
            "label": "Total Customers",
            "datatype": "Int"
        },
        {
            "value": total_revenue,
            "label": "Total Revenue",
            "datatype": "Currency"
        },
        {
            "value": overall_achievement,
            "label": "Overall Achievement",
            "datatype": "Percent",
            "indicator": "Green" if overall_achievement >= 100 else "Red"
        }
    ]
