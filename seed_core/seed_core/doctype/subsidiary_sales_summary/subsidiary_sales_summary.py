import frappe
from frappe.model.document import Document


class SubsidiarySalesSummary(Document):
    def before_save(self):
        # Auto-fetch subsidiary name if not set
        if self.subsidiary_code and not self.subsidiary_name:
            mapping = {
                "MA": "Yuksel Seeds Morocco",
                "ES": "Yuksel Seeds Spain",
                "TR": "Yuksel Tohum (Turkey)"
            }
            self.subsidiary_name = mapping.get(self.subsidiary_code, self.subsidiary_code)
        
        # Auto-fetch crop from seed variety
        if self.seed_variety and not self.crop:
            self.crop = frappe.db.get_value("Seed Variety", self.seed_variety, "crop")
