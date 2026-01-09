import frappe
from frappe import _

def setup_dashboards():
    """
    Creates standard Dashboards and Charts for Seed Company based on requirements.
    Run via: bench execute seed_core.setup.dashboards.setup_dashboards
    """
    create_sales_dashboard()
    create_stock_dashboard()
    create_regional_dashboards()
    frappe.db.commit()

def create_chart(name, chart_type, y_axis_field, label, sql_query, type="Bar"):
    if not frappe.db.exists("Dashboard Chart", name):
        doc = frappe.new_doc("Dashboard Chart")
        doc.chart_name = name
        doc.chart_type = type
        doc.source = "Custom" # or Report
        doc.timeseries = 0 
        doc.custom_options = "" 
        doc.type = chart_type
        # For simplicity in this script, we're assuming custom source or simplified configuration
        # Real implementation requires mapping strict SQL or Report logic
        doc.save()

def create_sales_dashboard():
    # Placeholder for Sales Dashboard Logic
    # 1. Total Sales Orders (Month)
    # 2. Sales by Crop (Pie Chart)
    if not frappe.db.exists("Dashboard", "Seed Sales Dashboard"):
        dash = frappe.new_doc("Dashboard")
        dash.dashboard_name = "Seed Sales Dashboard"
        dash.is_standard = 1
        dash.module = "Seed Core"
        dash.save()
        # Add charts links here if charts existed

def create_stock_dashboard():
    # Placeholder for Stock Dashboard Logic
    pass

def create_doctype_dashboards():
    """
    Configures standard dashboards for specific DocTypes (Batch, Seed Variety)
    """
    # Batch Dashboard (Lab Tests, Stock Moves)
    if not frappe.db.exists("Dashboard", "Batch Dashboard"):
        d = frappe.new_doc("Dashboard")
        d.dashboard_name = "Batch Dashboard"
        d.module = "Seed Core"
        d.is_standard = 1
        d.save()
        
    # Seed Variety Dashboard (Stock Level, Sales)
    if not frappe.db.exists("Dashboard", "Seed Variety Dashboard"):
        d = frappe.new_doc("Dashboard")
        d.dashboard_name = "Seed Variety Dashboard"
        d.module = "Seed Core"
        d.is_standard = 1
        d.save()

def create_regional_dashboards():
    # Create specific dashboards for:
    regions = ["Europe - Nico", "Maghreb - Nassir", "Poland - Oskar", "LATAM - Miguel"]
    for reg in regions:
        if not frappe.db.exists("Dashboard", f"Region: {reg}"):
            d = frappe.new_doc("Dashboard")
            d.dashboard_name = f"Region: {reg}"
            d.is_standard = 1
            d.module = "Seed Core"
            d.save()
