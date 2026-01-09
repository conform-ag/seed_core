import frappe

def after_install():
    """
    Called after the app is installed.
    Creates the Seed Core module definition if it doesn't exist.
    """
    create_module_def()
    frappe.db.commit()

def create_module_def():
    """Create the Seed Core module definition"""
    if not frappe.db.exists("Module Def", "Seed Core"):
        module = frappe.new_doc("Module Def")
        module.module_name = "Seed Core"
        module.app_name = "seed_core"
        module.insert(ignore_permissions=True)
        print("Created Module Def: Seed Core")
