import frappe

def execute(filters=None):
	columns = [
		{"label": "Item", "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": "Batch", "fieldname": "batch_id", "fieldtype": "Link", "options": "Batch", "width": 120},
		{"label": "Seed Variety", "fieldname": "seed_variety", "fieldtype": "Link", "options": "Seed Variety", "width": 150},
		{"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "width": 100},
		{"label": "Germination %", "fieldname": "germination_percent", "fieldtype": "Percent", "width": 100},
		{"label": "Test Status", "fieldname": "test_status", "fieldtype": "Data", "width": 100}
	]

	data = get_data(filters)
	return columns, data

def get_data(filters):
	# Mock data query logic
	# In real implementation: Join Bin/Batch with custom fields
	return frappe.db.sql("""
		SELECT 
			b.item as item_code,
			b.name as batch_id,
			b.seed_variety,
			(SELECT sum(actual_qty) FROM `tabBin` where batch_no = b.name) as qty,
			lt.germination_percent,
			lt.status as test_status
		FROM
			`tabBatch` b
		LEFT JOIN
			`tabLab Test` lt ON b.latest_lab_test = lt.name
		WHERE
			b.disabled = 0
	""", as_dict=True)
