# Copyright (c) 2026, aremtech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SeedProcessing(Document):
	def validate(self):
		self.calculate_loss()
		self.set_output_item()

	def calculate_loss(self):
		"""Calculate waste and loss percentage."""
		if self.input_qty and self.output_qty:
			self.waste_qty = self.input_qty - self.output_qty
			self.loss_percent = (self.waste_qty / self.input_qty) * 100 if self.input_qty > 0 else 0

	def set_output_item(self):
		"""Default output item to input item if not specified."""
		if not self.output_item:
			self.output_item = self.input_item

	def on_submit(self):
		"""Create Stock Entry and apply attribute inheritance."""
		self.create_stock_entry()
		self.apply_attribute_inheritance()

	def on_cancel(self):
		"""Cancel linked Stock Entry."""
		if self.stock_entry:
			se = frappe.get_doc("Stock Entry", self.stock_entry)
			if se.docstatus == 1:
				se.cancel()

	def create_stock_entry(self):
		"""Create Repack Stock Entry for processing."""
		# Create output batch if needed
		output_batch = self.output_batch
		if self.auto_create_batch and not output_batch:
			output_batch = self.create_output_batch()

		# Create Stock Entry
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Repack"
		se.company = self.company
		se.posting_date = self.posting_date

		# Input: consume from input batch
		se.append("items", {
			"item_code": self.input_item,
			"qty": self.input_qty,
			"s_warehouse": self.warehouse,
			"batch_no": self.input_batch
		})

		# Output: add to output batch
		se.append("items", {
			"item_code": self.output_item or self.input_item,
			"qty": self.output_qty,
			"t_warehouse": self.warehouse,
			"batch_no": output_batch,
			"is_finished_item": 1
		})

		se.seed_processing = self.name
		se.insert(ignore_permissions=True)
		se.submit()

		# Update reference
		frappe.db.set_value("Seed Processing", self.name, "stock_entry", se.name, update_modified=False)
		frappe.db.set_value("Seed Processing", self.name, "output_batch", output_batch, update_modified=False)
		self.stock_entry = se.name
		self.output_batch = output_batch

	def create_output_batch(self):
		"""Create a new batch for output."""
		item_code = self.output_item or self.input_item

		# Get operation suffix
		suffix_map = {
			"Cleaning": "C",
			"Grading": "G",
			"Priming": "PR",
			"Pelleting": "PL",
			"Chemical Treatment": "T",
			"Packaging": "PK"
		}
		suffix = suffix_map.get(self.operation_type, "P")

		# Generate batch name
		batch_name = f"{self.input_batch}-{suffix}"

		# Check if batch exists
		if frappe.db.exists("Batch", batch_name):
			count = 1
			while frappe.db.exists("Batch", f"{batch_name}{count}"):
				count += 1
			batch_name = f"{batch_name}{count}"

		batch = frappe.new_doc("Batch")
		batch.batch_id = batch_name
		batch.item = item_code
		batch.insert(ignore_permissions=True)

		return batch.name

	def apply_attribute_inheritance(self):
		"""Copy or set batch attributes based on operation type."""
		if not self.output_batch:
			return

		input_batch = frappe.get_doc("Batch", self.input_batch)

		# Copy biological data (Germination/Purity) from input to output
		fields_to_copy = [
			"germination_percent", "purity_percent", "moisture_percent",
			"seed_vigor", "lab_test_date", "next_retest_date",
			"is_organic", "is_gspp"
		]

		for field in fields_to_copy:
			if hasattr(input_batch, field):
				frappe.db.set_value("Batch", self.output_batch, field,
					getattr(input_batch, field), update_modified=False)

		# Apply treatment-specific attributes
		if self.operation_type == "Cleaning":
			# Cleaning resets treatment attributes
			pass
		elif self.operation_type == "Pelleting":
			frappe.db.set_value("Batch", self.output_batch, "is_pelleted", 1, update_modified=False)
		elif self.operation_type == "Priming":
			frappe.db.set_value("Batch", self.output_batch, "is_primed", 1, update_modified=False)
		elif self.operation_type == "Chemical Treatment":
			frappe.db.set_value("Batch", self.output_batch, "is_chemically_treated", 1, update_modified=False)

		# Copy existing treatment flags from input
		treatment_fields = ["is_pelleted", "is_primed", "is_coated", "is_chemically_treated", "treatment_name"]
		for field in treatment_fields:
			if hasattr(input_batch, field) and getattr(input_batch, field):
				# Don't overwrite if we just set it above
				current_value = frappe.db.get_value("Batch", self.output_batch, field)
				if not current_value:
					frappe.db.set_value("Batch", self.output_batch, field,
						getattr(input_batch, field), update_modified=False)


@frappe.whitelist()
def get_batch_query(doctype, txt, searchfield, start, page_len, filters):
	"""Get batches for the selected input item."""
	item = filters.get("item") if filters else None
	if not item:
		return []

	return frappe.db.sql("""
		SELECT name, batch_id
		FROM `tabBatch`
		WHERE item = %(item)s
		AND (name LIKE %(txt)s OR batch_id LIKE %(txt)s)
		LIMIT %(start)s, %(page_len)s
	""", {
		"item": item,
		"txt": f"%{txt}%",
		"start": start,
		"page_len": page_len
	})
