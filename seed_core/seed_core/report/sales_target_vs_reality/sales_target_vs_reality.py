import frappe
from frappe import _
from frappe.utils import flt, getdate, add_months
import math

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
            "fieldname": "crop",
            "label": _("Crop"),
            "fieldtype": "Link",
            "options": "Seed Crop",
            "width": 100
        },
        {
            "fieldname": "seed_variety",
            "label": _("Variety"),
            "fieldtype": "Link",
            "options": "Seed Variety",
            "width": 120
        },
        {
            "fieldname": "party",
            "label": _("Party"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "month",
            "label": _("Month"),
            "fieldtype": "Data",
            "width": 60
        },
        {
            "fieldname": "target_qty",
            "label": _("Target Qty"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "target_amount",
            "label": _("Target Amt"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "actual_qty",
            "label": _("Actual Qty"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "actual_amount",
            "label": _("Actual Amt"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "variance_qty",
            "label": _("Var Qty"),
            "fieldtype": "Float",
            "width": 80
        },
        {
            "fieldname": "variance_pct",
            "label": _("Var %"),
            "fieldtype": "Percent",
            "width": 70
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 90
        }
    ]

def get_data(filters):
    # 1. Fetch relevant Sales Target Plans
    plans = get_plans(filters)
    
    if not plans:
        return []

    # 2. Build detailed data rows (one per variety/party/month)
    data = []
    all_rows = []  # Collect all plan rows with party info
    
    for plan in plans:
        plan_rows = filter_plan_rows(plan, filters)
        for row in plan_rows:
            all_rows.append({
                "crop": row.crop,
                "seed_variety": row.seed_variety,
                "party": plan.party,
                "month": row.month,
                "target_qty": flt(row.forecast_qty),
                "target_amount": flt(row.forecast_amount),
            })
    
    # 3. Get actuals by variety/month
    actual_map = get_detailed_actuals(filters, plans)
    
    # 4. Build final data with actuals
    for row in all_rows:
        key = (row["seed_variety"], row["month"])
        actual_qty = actual_map.get(key, {}).get("qty", 0)
        actual_amount = actual_map.get(key, {}).get("amount", 0)
        
        variance_qty = actual_qty - row["target_qty"]
        variance_pct = (variance_qty / row["target_qty"] * 100) if row["target_qty"] else 0
        
        status = ""
        if variance_qty > 0:
            status = "Above"
        elif variance_qty < 0:
            status = "Below"
        else:
            status = "On Target"
        
        data.append({
            "crop": row["crop"],
            "seed_variety": row["seed_variety"],
            "party": row["party"],
            "month": row["month"],
            "target_qty": row["target_qty"],
            "target_amount": row["target_amount"],
            "actual_qty": actual_qty,
            "actual_amount": actual_amount,
            "variance_qty": variance_qty,
            "variance_pct": variance_pct,
            "status": status
        })
    
    # Sort by Crop, Variety, Month
    months_order = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6, 
                    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
    data.sort(key=lambda x: (x.get("crop") or "", x.get("seed_variety") or "", months_order.get(x.get("month"), 0)))

    return data

def get_plans(filters):
    conditions = {"docstatus": 1, "company": filters.get("company"), "fiscal_year": filters.get("fiscal_year")}
    
    if filters.get("customer"):
        conditions["party_type"] = "Customer"
        conditions["party"] = filters.get("customer")
    elif filters.get("country"):
        # If Country is selected, we want Plans for that Territory OR Plans for Customers in that Territory
        # This is complex. Let's simplify:
        # 1. Country Level Plans: party_type="Territory", party=Country
        # 2. Distributor Plans: party_type="Customer", party IN (Customers in Country)
        
        # We'll handle this manually via frappe.get_all or SQL.
        pass
    
    # Simple fetching for now, refine for Country/Hierarchy logic
    plans = frappe.get_all("Sales Target Plan", filters=conditions, fields=["name", "party_type", "party"])
    
    # If Country Filter is set, we need to add the hierarchy logic manually
    if filters.get("country") and not filters.get("customer"):
        country = filters.get("country")
        # Get all territories under this country
        territory_lft, territory_rgt = frappe.db.get_value("Territory", country, ["lft", "rgt"])
        
        # Find plans where party is territory in range OR party is customer in territory in range
        # Use SQL for this complex join/filter
        query = f"""
            SELECT name FROM `tabSales Target Plan`
            WHERE docstatus = 1 
            AND company = %(company)s 
            AND fiscal_year = %(fiscal_year)s
            AND (
                (party_type = 'Territory' AND party IN (SELECT name FROM `tabTerritory` WHERE lft >= {territory_lft} AND rgt <= {territory_rgt}))
                OR
                (party_type = 'Customer' AND party IN (SELECT name FROM `tabCustomer` WHERE territory IN (SELECT name FROM `tabTerritory` WHERE lft >= {territory_lft} AND rgt <= {territory_rgt})))
            )
        """
        plans = frappe.db.sql(query, filters, as_dict=True)

    loaded_plans = []
    for p in plans:
        loaded_plans.append(frappe.get_doc("Sales Target Plan", p.name))
        
    return loaded_plans

def filter_plan_rows(plan, filters):
    rows = []
    for row in plan.targets:
        # Filter by Crop
        if filters.get("crop") and row.crop != filters.get("crop"):
            continue
        # Filter by Variety
        if filters.get("seed_variety") and row.seed_variety != filters.get("seed_variety"):
            continue
            
        rows.append(row)
    return rows

def get_detailed_actuals(filters, plans):
    """Get actuals broken down by variety and month"""
    
    # Collect all varieties from plans
    varieties = set()
    for plan in plans:
        for row in plan.targets:
            if row.seed_variety:
                varieties.add(row.seed_variety)
    
    if not varieties:
        return {}
    
    # Time window
    fy = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
    
    # Scope Filter
    scope_condition = ""
    if filters.get("customer"):
        scope_condition = f"AND si.customer = '{filters.get('customer')}'"
    elif filters.get("country"):
        territory_lft, territory_rgt = frappe.db.get_value("Territory", filters.get("country"), ["lft", "rgt"])
        if territory_lft and territory_rgt:
            scope_condition = f"""
                AND si.territory IN (
                    SELECT name FROM `tabTerritory`
                    WHERE lft >= {territory_lft} AND rgt <= {territory_rgt}
                )
            """
    
    # Variety Filter
    valid_varieties = [v for v in varieties if v]
    if not valid_varieties:
        return {}
    
    formatted = "', '".join(valid_varieties)
    
    # Query
    query = f"""
        SELECT 
            sii.item_code as variety,
            DATE_FORMAT(si.posting_date, '%%b') as month,
            SUM(sii.qty) as qty,
            SUM(sii.amount) as amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1
            AND si.company = %(company)s
            AND si.posting_date BETWEEN %(year_start_date)s AND %(year_end_date)s
            AND sii.item_code IN ('{formatted}')
            {scope_condition}
        GROUP BY sii.item_code, DATE_FORMAT(si.posting_date, '%%b')
    """
    
    results = frappe.db.sql(query, {
        "company": filters.get("company"),
        "year_start_date": fy.year_start_date,
        "year_end_date": fy.year_end_date
    }, as_dict=True)
    
    # Build map: (variety, month) -> {qty, amount}
    actual_map = {}
    for row in results:
        key = (row.variety, row.month)
        actual_map[key] = {"qty": flt(row.qty), "amount": flt(row.amount)}
    
    return actual_map

def get_aggregated_actuals(filters, varieties):
    # Logic to fetch actual sales for the given scope and varieties
    
    # Time window
    fy = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
    
    # Scope Filter
    scope_condition = ""
    if filters.get("customer"):
        scope_condition = f"AND si.customer = '{filters.get('customer')}'"
    elif filters.get("country"):
        territory_lft, territory_rgt = frappe.db.get_value("Territory", filters.get("country"), ["lft", "rgt"])
        scope_condition = f"""
            AND si.territory IN (
                SELECT name FROM `tabTerritory`
                WHERE lft >= {territory_lft} AND rgt <= {territory_rgt}
            )
        """
        
    item_condition = ""
    if varieties:
        # Filter out None values
        valid_varieties = [v for v in varieties if v]
        if valid_varieties:
            formatted = "', '".join(valid_varieties)
            item_condition = f"AND sii.item_code IN ('{formatted}')"
    elif filters.get("seed_variety"):
         item_condition = f"AND sii.item_code = '{filters.get('seed_variety')}'"
         
    # Query
    query = f"""
        SELECT 
            DATE_FORMAT(si.posting_date, '%%b') as month,
            SUM(sii.qty) as qty,
            SUM(sii.amount) as amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1
            AND si.company = %(company)s
            AND si.posting_date BETWEEN %(year_start_date)s AND %(year_end_date)s
            {scope_condition}
            {item_condition}
        GROUP BY DATE_FORMAT(si.posting_date, '%%b')
    """
    
    results = frappe.db.sql(query, {
        "company": filters.get("company"),
        "year_start_date": fy.year_start_date,
        "year_end_date": fy.year_end_date
    }, as_dict=True)
    
    qty_map = {row.month: flt(row.qty) for row in results}
    amount_map = {row.month: flt(row.amount) for row in results}
    
    return qty_map, amount_map

def get_chart(data):
    if not data:
        return None
    
    # Aggregate data by month for chart
    months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    monthly_target_qty = {m: 0 for m in months_order}
    monthly_actual_qty = {m: 0 for m in months_order}
    monthly_target_amt = {m: 0 for m in months_order}
    monthly_actual_amt = {m: 0 for m in months_order}
    
    for row in data:
        month = row.get("month")
        if month in monthly_target_qty:
            monthly_target_qty[month] += flt(row.get("target_qty"))
            monthly_actual_qty[month] += flt(row.get("actual_qty"))
            monthly_target_amt[month] += flt(row.get("target_amount"))
            monthly_actual_amt[month] += flt(row.get("actual_amount"))
    
    return {
        "data": {
            "labels": months_order,
            "datasets": [
                {
                    "name": "Target Qty",
                    "values": [monthly_target_qty[m] for m in months_order],
                    "chartType": "bar",
                    "color": "#2490ef"
                },
                {
                    "name": "Actual Qty",
                    "values": [monthly_actual_qty[m] for m in months_order],
                    "chartType": "bar",
                    "color": "#28a745"
                }
            ]
        },
        "type": "bar",
        "colors": ["#2490ef", "#28a745"]
    }

@frappe.whitelist()
def get_dashboard_chart(data=None, filters=None):
    if not filters:
        filters = {}
        
    # Default to current Fiscal Year if not provided
    if not filters.get("fiscal_year"):
        current_fy = frappe.db.get_value("Fiscal Year", {"year_start_date": ["<=", frappe.utils.nowdate()], "year_end_date": [">=", frappe.utils.nowdate()]}, "name")
        if current_fy:
            filters["fiscal_year"] = current_fy
            
    # Default to user's company
    if not filters.get("company"):
        filters["company"] = frappe.defaults.get_user_default("Company")
        
    data = get_data(filters)
    chart = get_chart(data)
    
    return chart

def get_report_summary(data):
    if not data:
        return []
        
    total_target_qty = sum(row.get("target_qty", 0) for row in data)
    total_target_amount = sum(row.get("target_amount", 0) for row in data)
    total_actual_qty = sum(row.get("actual_qty", 0) for row in data)
    total_actual_amount = sum(row.get("actual_amount", 0) for row in data)
    
    variance_amount = total_actual_amount - total_target_amount
    
    return [
        {
            "value": total_target_qty,
            "label": "Target Qty",
            "datatype": "Float",
        },
        {
            "value": total_target_amount,
            "label": "Target Amount",
            "datatype": "Currency",
        },
        {
            "value": total_actual_qty,
            "label": "Actual Qty",
            "datatype": "Float",
        },
        {
            "value": total_actual_amount,
            "label": "Actual Amount",
            "datatype": "Currency",
        },
        {
            "value": variance_amount,
            "label": "Variance",
            "datatype": "Currency",
            "indicator": "Green" if variance_amount >= 0 else "Red"
        }
    ]
