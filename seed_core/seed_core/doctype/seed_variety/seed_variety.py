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

    # Virtual field: Total Stock Quantity across all warehouses
    @property
    def total_stock_qty(self):
        """Get total stock quantity from all Bins for this variety's Item"""
        if not frappe.db.exists("Item", self.variety_name):
            return 0
        
        result = frappe.db.sql("""
            SELECT SUM(actual_qty) as total_qty
            FROM `tabBin`
            WHERE item_code = %s
        """, (self.variety_name,), as_dict=True)
        
        return result[0].total_qty if result and result[0].total_qty else 0

    # Virtual field: Selling Price from default Price List
    @property
    def selling_price(self):
        """Get the selling price from the default selling price list"""
        if not frappe.db.exists("Item", self.variety_name):
            return 0
        
        # Get the default selling price list
        default_price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
        
        if not default_price_list:
            # Fallback to Standard Selling
            default_price_list = "Standard Selling"
        
        price = frappe.db.get_value(
            "Item Price",
            {
                "item_code": self.variety_name,
                "price_list": default_price_list,
                "selling": 1
            },
            "price_list_rate"
        )
        
        return price or 0
