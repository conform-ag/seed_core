import frappe
from frappe.model.document import Document

class LabTest(Document):
	def validate(self):
		if self.germination_percent and self.germination_percent < 0:
			frappe.throw("Germination cannot be negative")
		
		# Auto-set status example
		if self.germination_percent and self.germination_percent >= 85:
			if self.status == 'Pending':
				self.status = 'Pass'
