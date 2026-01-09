import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class SalesTargetPlan(Document):
    def validate(self):
        self.calculate_totals()
        self.calculate_delta_percent()

    def calculate_totals(self):
        """Calculate total history and forecast amounts"""
        self.total_history_qty = sum(flt(row.history_qty) for row in self.targets)
        self.total_history_amount = sum(flt(row.history_amount) for row in self.targets)
        self.total_forecast_qty = sum(flt(row.forecast_qty) for row in self.targets)
        self.total_forecast_amount = sum(flt(row.forecast_amount) for row in self.targets)

    def calculate_delta_percent(self):
        """Calculate delta percentage for each target row"""
        for row in self.targets:
            if flt(row.history_qty) > 0:
                row.delta_percent = ((flt(row.forecast_qty) - flt(row.history_qty)) / flt(row.history_qty)) * 100
            else:
                row.delta_percent = 100 if flt(row.forecast_qty) > 0 else 0

    @frappe.whitelist()
    def fetch_historical_data(self):
        """
        Fetch last year's sales data from Sales Invoice and populate the targets table.
        Called from client script when party and fiscal_year are selected.
        """
        if not self.fiscal_year or not self.party:
            return
        
        # Get previous fiscal year
        prev_year = self.get_previous_fiscal_year()
        if not prev_year:
            frappe.msgprint("Could not find previous fiscal year for historical data")
            return
        
        # Get historical sales data
        historical_data = self.get_sales_data(prev_year)
        
        # Clear existing targets and populate with historical data
        self.targets = []
        
        for row in historical_data:
            self.append("targets", {
                "item_code": row.item_code,
                "item_group": row.item_group,
                "month": row.month,
                "history_qty": row.qty,
                "history_amount": row.amount,
                "forecast_qty": row.qty,  # Pre-fill with history as baseline
                "forecast_amount": row.amount
            })
        
        if not historical_data:
            # If no history, add empty rows for each month
            months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
            for month in months:
                self.append("targets", {
                    "month": month,
                    "history_qty": 0,
                    "history_amount": 0,
                    "forecast_qty": 0,
                    "forecast_amount": 0
                })
        
        frappe.msgprint(f"Loaded {len(historical_data)} historical records from {prev_year}", indicator="green", alert=True)

    def get_previous_fiscal_year(self):
        """Get the fiscal year before the selected one"""
        current_fy = frappe.get_doc("Fiscal Year", self.fiscal_year)
        
        prev_year = frappe.db.get_value(
            "Fiscal Year",
            {"year_end_date": ["<", current_fy.year_start_date]},
            "name",
            order_by="year_end_date desc"
        )
        
        return prev_year

    def get_sales_data(self, fiscal_year):
        """
        Get aggregated sales data from Sales Invoice for the given fiscal year and party.
        Returns: [{item_code, item_group, month, qty, amount}, ...]
        """
        fy_doc = frappe.get_doc("Fiscal Year", fiscal_year)
        
        # Build party filter based on party_type
        party_filter = ""
        if self.party_type == "Customer":
            party_filter = "AND si.customer = %(party)s"
        elif self.party_type == "Customer Group":
            party_filter = "AND si.customer IN (SELECT name FROM `tabCustomer` WHERE customer_group = %(party)s)"
        elif self.party_type == "Territory":
            party_filter = "AND si.territory = %(party)s"
        
        query = f"""
            SELECT 
                sii.item_code,
                i.item_group,
                DATE_FORMAT(si.posting_date, '%%b') as month,
                SUM(sii.qty) as qty,
                SUM(sii.amount) as amount
            FROM `tabSales Invoice Item` sii
            JOIN `tabSales Invoice` si ON sii.parent = si.name
            LEFT JOIN `tabItem` i ON sii.item_code = i.name
            WHERE si.docstatus = 1
                AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND si.company = %(company)s
                {party_filter}
            GROUP BY sii.item_code, i.item_group, DATE_FORMAT(si.posting_date, '%%b')
            ORDER BY sii.item_code, MONTH(si.posting_date)
        """
        
        return frappe.db.sql(query, {
            "from_date": fy_doc.year_start_date,
            "to_date": fy_doc.year_end_date,
            "company": self.company,
            "party": self.party
        }, as_dict=True)


@frappe.whitelist()
def get_subsidiary_forecast(subsidiary, fiscal_year):
    """
    API for parent company to pull subsidiary's submitted forecasts.
    Used for two-level consolidation.
    """
    forecasts = frappe.get_all(
        "Sales Target Plan",
        filters={
            "party_type": "Customer",
            "party": subsidiary,
            "fiscal_year": fiscal_year,
            "docstatus": 1  # Only submitted plans
        },
        fields=["name"]
    )
    
    if not forecasts:
        return []
    
    # Get the latest submitted plan
    plan = frappe.get_doc("Sales Target Plan", forecasts[0].name)
    
    return [{
        "item_code": row.item_code,
        "month": row.month,
        "forecast_qty": row.forecast_qty,
        "forecast_amount": row.forecast_amount
    } for row in plan.targets]
