import frappe
from frappe.model.document import Document


class SeedVariety(Document):
    def validate(self):
        pass

    def after_insert(self):
        """Create an ERPNext Item when a new Seed Variety is created"""
        self.create_item_if_not_exists()

    def create_item_if_not_exists(self):
        """
        Creates an Item linked to this Seed Variety with proper defaults for seed management:
        - Batch tracking enabled
        - Stock item
        - Default UOM: Nos (seeds counted individually)
        """
        if frappe.db.exists("Item", self.variety_name):
            return

        # Get or create the Seeds item group
        item_group = self.get_or_create_item_group()

        item = frappe.new_doc("Item")
        item.item_code = self.variety_name
        item.item_name = self.variety_name
        item.item_group = item_group
        item.stock_uom = "Nos"
        item.is_stock_item = 1
        item.has_batch_no = 1
        item.create_new_batch = 1
        item.has_serial_no = 0
        item.description = f"Seed Variety: {self.variety_name}"
        
        # Add crop info to description if available
        if self.crop:
            item.description = f"{self.crop} - {self.variety_name}"
        
        item.insert(ignore_permissions=True)
        frappe.msgprint(f"Item '{self.variety_name}' created automatically", indicator="green", alert=True)

    def get_or_create_item_group(self):
        """Get or create the crop-based item group under Seeds"""
        # First ensure "Seeds" parent group exists
        if not frappe.db.exists("Item Group", "Seeds"):
            seeds_group = frappe.new_doc("Item Group")
            seeds_group.item_group_name = "Seeds"
            seeds_group.parent_item_group = "All Item Groups"
            seeds_group.insert(ignore_permissions=True)

        # Create crop-specific subgroup if crop is set
        if self.crop:
            crop_group_name = f"Seeds - {self.crop}"
            if not frappe.db.exists("Item Group", crop_group_name):
                crop_group = frappe.new_doc("Item Group")
                crop_group.item_group_name = crop_group_name
                crop_group.parent_item_group = "Seeds"
                crop_group.insert(ignore_permissions=True)
            return crop_group_name
        
        return "Seeds"
