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
            "width": 100
        },
        {
            "fieldname": "ly_actual",
            "label": _("LY Actuals"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "stat_forecast",
            "label": _("Stat Forecast (AI)"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "sales_target",
            "label": _("Sales Target (Goal)"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "actual_sales",
            "label": _("Actual Sales (Current)"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "variance",
            "label": _("Variance (Goal vs AI)"),
            "fieldtype": "Currency",
            "width": 120
        },
        {
            "fieldname": "status",
            "label": _("Status"),
            "fieldtype": "Data",
            "width": 150
        }
    ]

def get_data(filters):
    if not filters.get("sales_target_plan"):
        return []

    plan = frappe.get_doc("Sales Target Plan", filters.get("sales_target_plan"))
    
    # Get Historical Data (Last Year)
    history_map = {row.month: flt(row.history_amount) for row in plan.targets}
    
    # Get Target Data (Goal)
    target_map = {row.month: flt(row.forecast_amount) for row in plan.targets}
    
    # Calculate Exponential Smoothing (Forecast)
    # Using simple exponential smoothing on historical data to project current year trend
    # Ideally this runs on a longer series, but we'll use LY as baseline + logic
    # For this demo, let's assume we smooth LY to get "Stable LY" and apply a growth factor?
    # Or strict Exp Smoothing: S_t = alpha * Y_t + (1-alpha) * S_t-1
    # We will generate a "Statistical Forecast" based on LY data smoothed.
    
    stat_forecast_map = calculate_exponential_smoothing(history_map)
    
    # Get Current Actuals (Real-time Reality)
    current_actuals_map = get_current_actuals(plan)
    
    data = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    total_ly = 0
    total_stat = 0
    total_target = 0
    
    for month in months:
        ly = history_map.get(month, 0)
        stat = stat_forecast_map.get(month, 0)
        target = target_map.get(month, 0)
        actual = current_actuals_map.get(month, 0)
        variance = target - stat
        
        status = ""
        if variance > 0:
            status = "Aggressive (+)"
        elif variance < 0:
             status = "Conservative (-)"
        else:
            status = "Aligned"

        row = {
            "month": month,
            "ly_actual": ly,
            "stat_forecast": stat,
            "sales_target": target,
            "actual_sales": actual,
            "variance": variance,
            "status": status
        }
        data.append(row)
        
        total_ly += ly
        total_stat += stat
        total_target += target

    return data

def calculate_exponential_smoothing(history_map):
    # Simple Exponential Smoothing
    # Alpha: smoothing factor (0 < alpha < 1)
    alpha = 0.5 
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    forecast = {}
    last_val = 0
    
    # Initialize with average of first 3 months or similar? 
    # Or just start with first value.
    if months:
        last_val = history_map.get(months[0], 0)
    
    for month in months:
        actual = history_map.get(month, 0)
        if actual == 0 and last_val == 0:
            smoothed = 0
        else:
             smoothed = alpha * actual + (1 - alpha) * last_val
        
        # We apply a small growth assumption for "Next Year Forecast" based on this smoothing
        # Let's say +5% trend
        forecast[month] = smoothed * 1.05
        last_val = smoothed
        
    return forecast

def get_current_actuals(plan):
    # Fetch Sales Invoice data for the current plan period
    # Aggregated by month
    
    # Build party filter
    party_filter = ""
    if plan.party_type == "Customer":
        party_filter = "AND si.customer = %(party)s"
    elif plan.party_type == "Customer Group":
        party_filter = "AND si.customer IN (SELECT name FROM `tabCustomer` WHERE customer_group = %(party)s)"
    elif plan.party_type == "Territory":
         # Use Nested Set logic matching what we did in DocType
        territory_lft, territory_rgt = frappe.db.get_value("Territory", plan.party, ["lft", "rgt"])
        party_filter = f"""
            AND si.territory IN (
                SELECT name FROM `tabTerritory`
                WHERE lft >= {territory_lft} AND rgt <= {territory_rgt}
            )
        """

    # Filter by items (varieties) in the plan to ensure "Reality" matches "Target" scope
    varieties = [row.seed_variety for row in plan.targets]
    item_filter = ""
    if varieties:
        formatted_varieties = "', '".join(varieties)
        item_filter = f"AND sii.item_code IN ('{formatted_varieties}')"

    query = f"""
        SELECT 
            DATE_FORMAT(si.posting_date, '%%b') as month,
            SUM(sii.amount) as amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1
            AND si.company = %(company)s
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {party_filter}
            {item_filter}
        GROUP BY DATE_FORMAT(si.posting_date, '%%b')
    """
    
    results = frappe.db.sql(query, {
        "company": plan.company,
        "from_date": plan.from_date,
        "to_date": plan.to_date,
        "party": plan.party
    }, as_dict=True)
    
    return {row.month: flt(row.amount) for row in results}

def get_chart(data):
    if not data:
        return None
        
    labels = [row.get("month") for row in data]
    
    ly_data = [row.get("ly_actual") for row in data]
    stat_data = [row.get("stat_forecast") for row in data]
    target_data = [row.get("sales_target") for row in data]
    
    return {
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "name": "LY Actuals",
                    "values": ly_data,
                    "chartType": "line",
                    "color": "gray" # Context
                },
                {
                    "name": "Stat Forecast (AI)",
                    "values": stat_data,
                    "chartType": "line",
                    "lineOptions": {"regionFill": 0, "dotSize": 4, "dash": 1}, # Dotted-ish
                    "color": "orange" 
                },
                {
                    "name": "Sales Target (Goal)",
                    "values": target_data,
                    "chartType": "line",
                    "color": "blue" # Goal
                }
            ]
        },
        "type": "axis-mixed", # allows mixed charts
        # "height": 300
    }

def get_report_summary(data):
    if not data:
        return []
        
    total_target = sum(row.get("sales_target") for row in data)
    total_forecast = sum(row.get("stat_forecast") for row in data)
    
    variance = total_target - total_forecast
    label = "Aggressive" if variance > 0 else "Conservative"
    
    return [
        {
            "value": total_target,
            "label": "Total Target",
            "datatype": "Currency",
        },
        {
            "value": total_forecast,
            "label": "AI Forecast",
            "datatype": "Currency",
        },
        {
            "value": variance,
            "label": f"Variance ({label})",
            "datatype": "Currency",
            "indicator": "Green" if variance > 0 else "Red"
        }
    ]
