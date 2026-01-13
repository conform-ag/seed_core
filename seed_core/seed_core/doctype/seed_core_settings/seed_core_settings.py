import frappe
from frappe.model.document import Document


class SeedCoreSettings(Document):
    def validate(self):
        if self.site_type == "Subsidiary" and not self.subsidiary_code:
            frappe.throw("Subsidiary Code is required for Subsidiary sites")
    
    def is_parent_site(self):
        return self.site_type == "Parent Company"
    
    def is_subsidiary_site(self):
        return self.site_type == "Subsidiary"
