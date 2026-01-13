import frappe
from frappe.model.document import Document


class SeedVariety(Document):
    def validate(self):
        pass

    def after_insert(self):
        """Create an ERPNext Item when a new Seed Variety is created"""
        self.create_item_if_not_exists()

    @frappe.whitelist()
    def sync_item(self):
        """Manually trigger item creation/update"""
        self.create_item_if_not_exists()
        frappe.msgprint(f"Item synced for {self.variety_name}", indicator="green", alert=True)

    def create_item_if_not_exists(self):
        """
        Creates or Updates an Item linked to this Seed Variety.
        Syncs: Image, Description, Crop (Item Group)
        """
        item_group = self.get_or_create_item_group()
        
        if frappe.db.exists("Item", self.variety_name):
            item = frappe.get_doc("Item", self.variety_name)
        else:
            item = frappe.new_doc("Item")
            item.item_code = self.variety_name
            item.stock_uom = "Nos"
            item.is_stock_item = 1
            item.has_batch_no = 1
            item.create_new_batch = 1
            item.has_serial_no = 0
            
        # Update fields that should be synced
        item.item_name = self.variety_name
        item.item_group = item_group
        item.description = f"Seed Variety: {self.variety_name}"
        if self.crop:
            item.description = f"{self.crop} - {self.variety_name}"
            
        if self.image:
            item.image = self.image
            
        item.save(ignore_permissions=True)

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


@frappe.whitelist()
def get_stock_details(variety_name):
    """Get stock details by warehouse and batch for a seed variety"""
    if not variety_name or not frappe.db.exists("Item", variety_name):
        return []
    
    data = frappe.db.sql("""
        SELECT 
            b.warehouse,
            b.actual_qty,
            i.stock_uom,
            sle.batch_no,
            batch.expiry_date
        FROM `tabBin` b
        LEFT JOIN `tabItem` i ON i.name = b.item_code
        LEFT JOIN (
            SELECT batch_no, warehouse, item_code
            FROM `tabStock Ledger Entry`
            WHERE item_code = %(item_code)s AND actual_qty > 0
            GROUP BY batch_no, warehouse
        ) sle ON sle.warehouse = b.warehouse
        LEFT JOIN `tabBatch` batch ON batch.name = sle.batch_no
        WHERE b.item_code = %(item_code)s AND b.actual_qty > 0
        ORDER BY b.warehouse, sle.batch_no
    """, {"item_code": variety_name}, as_dict=True)
    
    return data


@frappe.whitelist()
def get_sales_transactions(variety_name):
    """Get sales transactions for a seed variety"""
    if not variety_name or not frappe.db.exists("Item", variety_name):
        return {"sales_orders": [], "sales_invoices": [], "delivery_notes": []}
    
    # Sales Orders
    sales_orders = frappe.db.sql("""
        SELECT 
            so.name, 
            so.transaction_date as date,
            so.customer as party,
            soi.qty,
            soi.amount,
            so.status
        FROM `tabSales Order` so
        JOIN `tabSales Order Item` soi ON soi.parent = so.name
        WHERE soi.item_code = %(item_code)s AND so.docstatus = 1
        ORDER BY so.transaction_date DESC
        LIMIT 20
    """, {"item_code": variety_name}, as_dict=True)
    
    # Sales Invoices
    sales_invoices = frappe.db.sql("""
        SELECT 
            si.name,
            si.posting_date as date,
            si.customer as party,
            sii.qty,
            sii.amount,
            si.status
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE sii.item_code = %(item_code)s AND si.docstatus = 1
        ORDER BY si.posting_date DESC
        LIMIT 20
    """, {"item_code": variety_name}, as_dict=True)
    
    # Delivery Notes
    delivery_notes = frappe.db.sql("""
        SELECT 
            dn.name,
            dn.posting_date as date,
            dn.customer as party,
            dni.qty,
            dni.amount,
            dn.status
        FROM `tabDelivery Note` dn
        JOIN `tabDelivery Note Item` dni ON dni.parent = dn.name
        WHERE dni.item_code = %(item_code)s AND dn.docstatus = 1
        ORDER BY dn.posting_date DESC
        LIMIT 20
    """, {"item_code": variety_name}, as_dict=True)
    
    return {
        "sales_orders": sales_orders,
        "sales_invoices": sales_invoices,
        "delivery_notes": delivery_notes
    }


@frappe.whitelist()
def get_purchase_transactions(variety_name):
    """Get purchase transactions for a seed variety"""
    if not variety_name or not frappe.db.exists("Item", variety_name):
        return {"purchase_receipts": [], "purchase_invoices": []}
    
    # Purchase Receipts
    purchase_receipts = frappe.db.sql("""
        SELECT 
            pr.name,
            pr.posting_date as date,
            pr.supplier as party,
            pri.qty,
            pri.amount,
            pr.status
        FROM `tabPurchase Receipt` pr
        JOIN `tabPurchase Receipt Item` pri ON pri.parent = pr.name
        WHERE pri.item_code = %(item_code)s AND pr.docstatus = 1
        ORDER BY pr.posting_date DESC
        LIMIT 20
    """, {"item_code": variety_name}, as_dict=True)
    
    # Purchase Invoices
    purchase_invoices = frappe.db.sql("""
        SELECT 
            pi.name,
            pi.posting_date as date,
            pi.supplier as party,
            pii.qty,
            pii.amount,
            pi.status
        FROM `tabPurchase Invoice` pi
        JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
        WHERE pii.item_code = %(item_code)s AND pi.docstatus = 1
        ORDER BY pi.posting_date DESC
        LIMIT 20
    """, {"item_code": variety_name}, as_dict=True)
    
    return {
        "purchase_receipts": purchase_receipts,
        "purchase_invoices": purchase_invoices
    }
