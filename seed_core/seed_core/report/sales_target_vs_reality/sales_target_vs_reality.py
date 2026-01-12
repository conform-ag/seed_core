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
            "fieldname": "month",
            "label": _("Month"),
            "fieldtype": "Data",
            "width": 80
        },
        {
            "fieldname": "ly_qty",
            "label": _("LY Qty"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "ly_amount",
            "label": _("LY Amount"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "target_qty",
            "label": _("Target Qty"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "target_amount",
            "label": _("Target Amount"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "actual_qty",
            "label": _("Actual Qty"),
            "fieldtype": "Float",
            "width": 90
        },
        {
            "fieldname": "actual_amount",
            "label": _("Actual Amount"),
            "fieldtype": "Currency",
            "width": 110
        },
        {
            "fieldname": "variance_qty",
            "label": _("Var Qty"),
            "fieldtype": "Float",
            "width": 80
        },
        {
            "fieldname": "variance_amount",
            "label": _("Var Amount"),
            "fieldtype": "Currency",
            "width": 100
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 100
        }
    ]

def get_data(filters):
    # 1. Fetch relevant Sales Target Plans
    plans = get_plans(filters)
    
    if not plans:
        return []

    # 2. Initialize Aggregators (qty and amount)
    history_qty_map = {}
    history_amount_map = {}
    target_qty_map = {}
    target_amount_map = {}
    total_varieties = set()
    
    # 3. Aggregate Data from Plans
    for plan in plans:
        plan_rows = filter_plan_rows(plan, filters)
        
        for row in plan_rows:
            month = row.month
            history_qty_map[month] = history_qty_map.get(month, 0) + flt(row.history_qty)
            history_amount_map[month] = history_amount_map.get(month, 0) + flt(row.history_amount)
            target_qty_map[month] = target_qty_map.get(month, 0) + flt(row.forecast_qty)
            target_amount_map[month] = target_amount_map.get(month, 0) + flt(row.forecast_amount)
            if row.seed_variety:
                total_varieties.add(row.seed_variety)

    # 4. Get Current Actuals (Reality) - Filtered by relevant Varieties & Scope
    actual_qty_map, actual_amount_map = get_aggregated_actuals(filters, total_varieties)
    
    # 5. Build Final Data Rows
    data = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    for month in months:
        ly_qty = history_qty_map.get(month, 0)
        ly_amount = history_amount_map.get(month, 0)
        target_qty = target_qty_map.get(month, 0)
        target_amount = target_amount_map.get(month, 0)
        actual_qty = actual_qty_map.get(month, 0)
        actual_amount = actual_amount_map.get(month, 0)
        
        variance_qty = actual_qty - target_qty
        variance_amount = actual_amount - target_amount
        
        status = ""
        if variance_amount > 0:
            status = "Above Target"
        elif variance_amount < 0:
            status = "Below Target"
        else:
            status = "On Target"

        row = {
            "month": month,
            "ly_qty": ly_qty,
            "ly_amount": ly_amount,
            "target_qty": target_qty,
            "target_amount": target_amount,
            "actual_qty": actual_qty,
            "actual_amount": actual_amount,
            "variance_qty": variance_qty,
            "variance_amount": variance_amount,
            "status": status
        }
        data.append(row)

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

def calculate_exponential_smoothing(history_map):
    alpha = 0.5 
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    forecast = {}
    last_val = history_map.get(months[0], 0) if months else 0
    
    for month in months:
        actual = history_map.get(month, 0)
        if actual == 0 and last_val == 0:
            smoothed = 0
        else:
             smoothed = alpha * actual + (1 - alpha) * last_val
        
        forecast[month] = smoothed * 1.05
        last_val = smoothed
        
    return forecast

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
        
    labels = [row.get("month") for row in data]
    
    ly_data = [row.get("ly_amount") for row in data]
    target_data = [row.get("target_amount") for row in data]
    actual_data = [row.get("actual_amount") for row in data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "LY Amount",
                    "values": ly_data,
                    "chartType": "line",
                    "color": "gray"
                },
                {
                    "name": "Target Amount",
                    "values": target_data,
                    "chartType": "line",
                    "color": "blue"
                },
                {
                    "name": "Actual Amount",
                    "values": actual_data,
                    "chartType": "bar",
                    "color": "green"
                }
            ]
        },
        "type": "axis-mixed"
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
