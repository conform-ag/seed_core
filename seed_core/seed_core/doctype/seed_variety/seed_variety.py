# Copyright (c) 2026, aremtech and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class SeedVariety(Document):
	def before_save(self):
		"""Generate variety identifier if not set."""
		if not self.variety_identifier:
			self.variety_identifier = self.generate_variety_identifier()

	def after_insert(self):
		"""Create linked ERPNext Item after variety is created."""
		self.create_or_update_linked_item()

	def on_update(self):
		"""Sync changes to linked ERPNext Item."""
		if self.linked_item:
			self.create_or_update_linked_item()

	def generate_variety_identifier(self):
		"""Generate unique variety identifier from hierarchy."""
		crop_code = frappe.db.get_value("Seed Crop", self.seed_crop, "crop_code") or "00"
		segment_code = frappe.db.get_value("Seed Segment", self.seed_segment, "segment_code") or "000"
		subsegment_code = "000"
		if self.seed_subsegment:
			subsegment_code = frappe.db.get_value("Seed SubSegment", self.seed_subsegment, "subsegment_code") or "000"
			# Extract just the subsegment part (last 2 digits)
			if "-" in subsegment_code:
				subsegment_code = subsegment_code.split("-")[-1]

		return f"{crop_code}-{segment_code}-{subsegment_code}-{self.variety_code}"

	def create_or_update_linked_item(self):
		"""Create or update the linked ERPNext Item."""
		# Get default settings
		settings = frappe.get_single("Seed Core Settings") if frappe.db.exists("DocType", "Seed Core Settings") else None
		default_item_group = settings.default_item_group if settings and settings.default_item_group else "Seeds"

		# Get crop name for item group (use crop as item group)
		crop_name = frappe.db.get_value("Seed Crop", self.seed_crop, "crop_name") or default_item_group

		# Ensure item group exists
		if not frappe.db.exists("Item Group", crop_name):
			# Use default if crop item group doesn't exist
			crop_name = default_item_group
			if not frappe.db.exists("Item Group", crop_name):
				# Create default Seeds item group if it doesn't exist
				item_group = frappe.new_doc("Item Group")
				item_group.item_group_name = crop_name
				item_group.parent_item_group = "All Item Groups"
				item_group.insert(ignore_permissions=True)

		if self.linked_item and frappe.db.exists("Item", self.linked_item):
			# Update existing item
			item = frappe.get_doc("Item", self.linked_item)
			item.item_name = self.variety_name
			item.description = self.get_item_description()
			item.item_group = crop_name
			item.save(ignore_permissions=True)
		else:
			# Create new item
			item = frappe.new_doc("Item")
			item.item_code = self.variety_identifier
			item.item_name = self.variety_name
			item.item_group = crop_name
			item.stock_uom = "Kg"
			item.is_stock_item = 1
			item.has_batch_no = 1
			item.create_new_batch = 1
			item.description = self.get_item_description()
			item.insert(ignore_permissions=True)

			# Update linked_item field
			frappe.db.set_value("Seed Variety", self.name, "linked_item", item.name, update_modified=False)
			self.linked_item = item.name

	def get_item_description(self):
		"""Generate item description from variety details."""
		parts = [f"Variety: {self.variety_name}"]

		if self.seed_crop:
			crop_name = frappe.db.get_value("Seed Crop", self.seed_crop, "crop_name")
			if crop_name:
				parts.append(f"Crop: {crop_name}")

		if self.seed_segment:
			segment_name = frappe.db.get_value("Seed Segment", self.seed_segment, "segment_name")
			if segment_name:
				parts.append(f"Segment: {segment_name}")

		if self.lifecycle_stage:
			parts.append(f"Stage: {self.lifecycle_stage}")

		if self.resistances:
			parts.append(f"Resistances: {self.resistances}")

		return "\n".join(parts)

	@frappe.whitelist()
	def sync_to_item(self):
		"""Manual trigger to sync variety to Item."""
		self.create_or_update_linked_item()
		frappe.msgprint(_("Synced to Item {0}").format(self.linked_item))
