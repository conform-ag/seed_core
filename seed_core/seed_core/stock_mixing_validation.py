# Copyright (c) 2026, aremtech and contributors
# For license information, please see license.txt

"""
Stock Mixing Validation for Seed Core

This module implements validation to prevent mixing incompatible batches
in the same warehouse bin (e.g., Organic with Chemically Treated).
"""

import frappe
from frappe import _


def validate_stock_mixing(doc, method=None):
	"""
	Validate that stock movements don't mix incompatible batch attributes.
	Called on Stock Entry and Stock Reconciliation validation.
	"""
	if doc.doctype not in ["Stock Entry", "Stock Reconciliation"]:
		return

	# Get settings
	settings = None
	if frappe.db.exists("DocType", "Seed Core Settings"):
		settings = frappe.get_single("Seed Core Settings")

	for item in doc.items:
		if not item.get("batch_no") or not item.get("t_warehouse"):
			continue

		# Get the incoming batch attributes
		incoming_batch = frappe.db.get_value(
			"Batch",
			item.batch_no,
			["is_organic", "is_chemically_treated", "is_pelleted", "is_primed", "is_coated"],
			as_dict=True
		)

		if not incoming_batch:
			continue

		# Check existing batches in target warehouse
		existing_batches = get_existing_batches_in_bin(item.item_code, item.t_warehouse, item.batch_no)

		for existing_batch in existing_batches:
			conflicts = check_attribute_conflicts(incoming_batch, existing_batch)
			if conflicts:
				handle_conflict(conflicts, item, existing_batch, settings)


def get_existing_batches_in_bin(item_code, warehouse, exclude_batch=None):
	"""Get batches with positive stock in the specified bin."""
	conditions = ""
	if exclude_batch:
		conditions = f"AND sle.batch_no != '{exclude_batch}'"

	batches = frappe.db.sql("""
		SELECT
			b.name as batch_no,
			b.is_organic,
			b.is_chemically_treated,
			b.is_pelleted,
			b.is_primed,
			b.is_coated,
			SUM(sle.actual_qty) as qty
		FROM `tabStock Ledger Entry` sle
		JOIN `tabBatch` b ON sle.batch_no = b.name
		WHERE sle.item_code = %(item_code)s
		AND sle.warehouse = %(warehouse)s
		AND sle.is_cancelled = 0
		{conditions}
		GROUP BY sle.batch_no
		HAVING SUM(sle.actual_qty) > 0
	""".format(conditions=conditions), {
		"item_code": item_code,
		"warehouse": warehouse
	}, as_dict=True)

	return batches


def check_attribute_conflicts(incoming, existing):
	"""
	Check for conflicts between incoming and existing batch attributes.
	Returns list of conflict descriptions.
	"""
	conflicts = []

	# Organic vs Chemically Treated conflict
	if incoming.get("is_organic") and existing.get("is_chemically_treated"):
		conflicts.append(_("Organic batch cannot be mixed with Chemically Treated batch"))

	if incoming.get("is_chemically_treated") and existing.get("is_organic"):
		conflicts.append(_("Chemically Treated batch cannot be mixed with Organic batch"))

	# Organic vs any treatment conflict
	if incoming.get("is_organic"):
		if existing.get("is_pelleted") or existing.get("is_primed") or existing.get("is_coated"):
			conflicts.append(_("Organic batch cannot be mixed with treated (Pelleted/Primed/Coated) batch"))

	if existing.get("is_organic"):
		if incoming.get("is_pelleted") or incoming.get("is_primed") or incoming.get("is_coated"):
			conflicts.append(_("Treated batch cannot be mixed with Organic batch"))

	return conflicts


def handle_conflict(conflicts, item, existing_batch, settings):
	"""Handle detected conflicts based on settings."""
	conflict_msg = _("Stock Mixing Conflict in {0}").format(item.t_warehouse)
	conflict_details = "\n".join([
		_("• Batch {0}: {1}").format(item.batch_no, c) for c in conflicts
	])
	conflict_details += "\n" + _("Existing batch in bin: {0}").format(existing_batch.batch_no)

	# Check safety stock logic setting
	if settings and settings.safety_stock_logic == "Warning":
		frappe.msgprint(
			msg=f"{conflict_msg}\n\n{conflict_details}",
			title=_("Stock Mixing Warning"),
			indicator="orange"
		)
	else:
		# Default to blocking
		frappe.throw(
			msg=f"{conflict_msg}\n\n{conflict_details}",
			title=_("Stock Mixing Error")
		)


def setup_hooks():
	"""
	Return the doc_events configuration for hooks.py.
	Add this to hooks.py:

	doc_events = {
		"Stock Entry": {
			"validate": "seed_core.seed_core.stock_mixing_validation.validate_stock_mixing"
		},
		"Stock Reconciliation": {
			"validate": "seed_core.seed_core.stock_mixing_validation.validate_stock_mixing"
		}
	}
	"""
	pass
