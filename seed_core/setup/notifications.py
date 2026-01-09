import frappe

def setup_notifications():
    """
    Creates standard Notifications for Seed Company.
    Run via: bench execute seed_core.setup.notifications.setup_notifications
    """
    create_sales_notifications()
    create_stock_notifications()
    frappe.db.commit()

def create_notification(name, subject, doc_type, event, condition, recipients, message):
    if not frappe.db.exists("Notification", name):
        doc = frappe.new_doc("Notification")
        doc.name = name
        doc.subject = subject
        doc.document_type = doc_type
        doc.event = event
        doc.condition = condition
        doc.channel = "Email"
        
        for r in recipients:
            doc.append("recipients", {
                "receiver_by": "Email",
                "email_ids": r
            })
            
        doc.message = message
        doc.save()

def create_sales_notifications():
    # 1.1 Sales Order Creation
    create_notification(
        name="New Sales Order Submitted",
        subject="New Sales Order Submitted: {{ doc.name }}",
        doc_type="Sales Order",
        event="Submit",
        condition="doc.docstatus==1",
        recipients=["manager@seedcompany.com", "logistics@seedcompany.com"],
        message="A new Sales Order {{ doc.name }} has been submitted."
    )
    
    # 1.3 Delayed Sales Orders (Scheduled)
    # Note: Scheduled alerts are handled differently (Alerts), simple setup here

def create_stock_notifications():
    # 3.1 Low Stock Alert
    create_notification(
        name="Low Stock Alert",
        subject="Low Stock Alert: {{ doc.item_code }}",
        doc_type="Bin",
        event="Save",
        condition="doc.actual_qty < doc.stock_uom", # Simplified logic
        recipients=["stock@seedcompany.com"],
        message="Item {{ doc.item_code }} is below reorder level."
    )
    
    # Custom: Critical Varieties
    create_notification(
        name="Critical Variety Alert",
        subject="Critical Variety Alert: {{ doc.item_code }}",
        doc_type="Bin",
        event="Save",
        condition="doc.item_code in ['Sweetloom', 'Kapia'] and doc.actual_qty < 100",
        recipients=["sales@seedcompany.com"],
        message="Critical variety {{ doc.item_code }} is running low!"
    )
