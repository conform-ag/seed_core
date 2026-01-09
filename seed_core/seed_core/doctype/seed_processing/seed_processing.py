import frappe
from frappe.model.document import Document
from frappe.utils import getdate

class SeedProcessing(Document):
	def validate(self):
		if self.input_qty < (self.output_qty + (self.waste_qty or 0)):
			frappe.msgprint("Warning: Output + Waste exceeds Input Qty")

	def on_submit(self):
		self.create_stock_entry()

	def create_stock_entry(self):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Repack" if self.operation == "Packing" else "Manufacture"
		se.purpose = se.stock_entry_type
		# Logic to populate items would go here
		# se.append("items", { ... input ... })
		# se.append("items", { ... output ... })
		# se.insert()
		# se.submit()
		frappe.msgprint(f"Stock Entry created: {se.name} (Simulated)")

@frappe.whitelist()
def get_batch_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select name from `tabBatch` where item = %s""", filters.get("input_item"))
