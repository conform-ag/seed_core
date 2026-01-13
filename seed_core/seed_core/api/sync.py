"""
Seed Core Sync API
Handles data synchronization between parent and subsidiary sites
"""
import frappe
from frappe import _
from frappe.utils import now_datetime


# ============================================
# PARENT SITE ENDPOINTS
# ============================================

@frappe.whitelist()
def get_targets_for_subsidiary(subsidiary_code, fiscal_year):
    """
    Called by subsidiary to fetch their targets from parent.
    Returns Sales Target Plans assigned to the subsidiary's territory.
    """
    settings = frappe.get_single("Seed Core Settings")
    
    if settings.site_type != "Parent Company":
        frappe.throw(_("This endpoint is only available on parent site"))
    
    # Get territory for this subsidiary
    # Assuming subsidiary_code maps to a Territory name
    territory = get_territory_for_subsidiary(subsidiary_code)
    
    if not territory:
        return {"success": False, "error": f"No territory found for subsidiary: {subsidiary_code}"}
    
    # Fetch submitted plans for this territory
    plans = frappe.get_all(
        "Sales Target Plan",
        filters={
            "docstatus": 1,
            "fiscal_year": fiscal_year,
            "target_level": "Territory",
            "party": territory
        },
        fields=["name", "fiscal_year", "company", "from_date", "to_date"]
    )
    
    result = []
    for plan_data in plans:
        plan = frappe.get_doc("Sales Target Plan", plan_data.name)
        targets = []
        for row in plan.targets:
            targets.append({
                "crop": row.crop,
                "seed_variety": row.seed_variety,
                "month": row.month,
                "target_qty": row.forecast_qty,
                "target_amount": row.forecast_amount
            })
        
        result.append({
            "plan_id": plan.name,
            "fiscal_year": plan.fiscal_year,
            "from_date": str(plan.from_date) if plan.from_date else None,
            "to_date": str(plan.to_date) if plan.to_date else None,
            "targets": targets
        })
    
    return {"success": True, "plans": result}


@frappe.whitelist()
def receive_subsidiary_actuals(data):
    """
    Called by subsidiary to push their sales actuals to parent.
    Creates/updates Subsidiary Sales Summary records.
    """
    settings = frappe.get_single("Seed Core Settings")
    
    if settings.site_type != "Parent Company":
        frappe.throw(_("This endpoint is only available on parent site"))
    
    if isinstance(data, str):
        import json
        data = json.loads(data)
    
    subsidiary_code = data.get("subsidiary_code")
    fiscal_year = data.get("fiscal_year")
    actuals = data.get("actuals", [])
    
    if not subsidiary_code or not fiscal_year:
        return {"success": False, "error": "Missing subsidiary_code or fiscal_year"}
    
    created = 0
    updated = 0
    
    for row in actuals:
        existing = frappe.db.exists("Subsidiary Sales Summary", {
            "subsidiary_code": subsidiary_code,
            "fiscal_year": fiscal_year,
            "seed_variety": row.get("seed_variety"),
            "month": row.get("month")
        })
        
        if existing:
            doc = frappe.get_doc("Subsidiary Sales Summary", existing)
            doc.qty = row.get("qty", 0)
            doc.amount = row.get("amount", 0)
            doc.synced_on = now_datetime()
            doc.save(ignore_permissions=True)
            updated += 1
        else:
            doc = frappe.new_doc("Subsidiary Sales Summary")
            doc.subsidiary_code = subsidiary_code
            doc.fiscal_year = fiscal_year
            doc.seed_variety = row.get("seed_variety")
            doc.month = row.get("month")
            doc.qty = row.get("qty", 0)
            doc.amount = row.get("amount", 0)
            doc.synced_on = now_datetime()
            doc.insert(ignore_permissions=True)
            created += 1
    
    frappe.db.commit()
    
    return {
        "success": True,
        "created": created,
        "updated": updated,
        "message": f"Synced {created + updated} records"
    }


def get_territory_for_subsidiary(subsidiary_code):
    """Map subsidiary code to territory name"""
    # This could be stored in a mapping table or derived from territory
    mapping = {
        "MA": "Morocco",
        "ES": "Spain",
        "TR": "Turkey"
    }
    return mapping.get(subsidiary_code)


# ============================================
# SUBSIDIARY SITE ENDPOINTS
# ============================================

@frappe.whitelist()
def pull_targets_from_parent():
    """
    Called on subsidiary to fetch targets from parent site.
    Creates local Sales Target Plan documents.
    """
    settings = frappe.get_single("Seed Core Settings")
    
    if settings.site_type != "Subsidiary":
        frappe.throw(_("This function is only for subsidiary sites"))
    
    if not settings.parent_site_url or not settings.api_key:
        frappe.throw(_("Parent site URL and API credentials not configured"))
    
    # Make API call to parent
    import requests
    
    fiscal_year = frappe.defaults.get_user_default("Fiscal Year")
    
    url = f"{settings.parent_site_url}/api/method/seed_core.api.sync.get_targets_for_subsidiary"
    headers = {
        "Authorization": f"token {settings.api_key}:{settings.get_password('api_secret')}"
    }
    params = {
        "subsidiary_code": settings.subsidiary_code,
        "fiscal_year": fiscal_year
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if not result.get("message", {}).get("success"):
            return {"success": False, "error": result.get("message", {}).get("error", "Unknown error")}
        
        plans = result.get("message", {}).get("plans", [])
        created = 0
        updated = 0
        
        for plan_data in plans:
            # Check if already synced
            existing = frappe.db.exists("Sales Target Plan", {
                "parent_plan_id": plan_data.get("plan_id"),
                "is_from_parent": 1
            })
            
            if existing:
                # Update existing
                doc = frappe.get_doc("Sales Target Plan", existing)
                doc.targets = []
                for target in plan_data.get("targets", []):
                    doc.append("targets", {
                        "crop": target.get("crop"),
                        "seed_variety": target.get("seed_variety"),
                        "month": target.get("month"),
                        "forecast_qty": target.get("target_qty"),
                        "forecast_amount": target.get("target_amount")
                    })
                doc.synced_on = now_datetime()
                doc.save(ignore_permissions=True)
                updated += 1
            else:
                # Create new
                doc = frappe.new_doc("Sales Target Plan")
                doc.fiscal_year = plan_data.get("fiscal_year")
                doc.company = frappe.defaults.get_user_default("Company")
                doc.target_level = "Territory"
                doc.party_type = "Territory"
                doc.party = settings.subsidiary_code  # Or map to local territory
                doc.is_from_parent = 1
                doc.parent_plan_id = plan_data.get("plan_id")
                doc.synced_on = now_datetime()
                
                if plan_data.get("from_date"):
                    doc.from_date = plan_data.get("from_date")
                if plan_data.get("to_date"):
                    doc.to_date = plan_data.get("to_date")
                
                for target in plan_data.get("targets", []):
                    doc.append("targets", {
                        "crop": target.get("crop"),
                        "seed_variety": target.get("seed_variety"),
                        "month": target.get("month"),
                        "forecast_qty": target.get("target_qty"),
                        "forecast_amount": target.get("target_amount")
                    })
                
                doc.insert(ignore_permissions=True)
                created += 1
        
        # Update last sync timestamp
        settings.last_sync_on = now_datetime()
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "created": created,
            "updated": updated,
            "message": f"Synced {created + updated} plans from parent"
        }
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


@frappe.whitelist()
def push_actuals_to_parent():
    """
    Called on subsidiary to push sales actuals to parent site.
    Aggregates from Sales Invoices and sends monthly summaries.
    """
    settings = frappe.get_single("Seed Core Settings")
    
    if settings.site_type != "Subsidiary":
        frappe.throw(_("This function is only for subsidiary sites"))
    
    if not settings.parent_site_url or not settings.api_key:
        frappe.throw(_("Parent site URL and API credentials not configured"))
    
    fiscal_year = frappe.defaults.get_user_default("Fiscal Year")
    fy = frappe.get_doc("Fiscal Year", fiscal_year)
    
    # Aggregate sales by variety and month
    query = """
        SELECT 
            sii.item_code as seed_variety,
            DATE_FORMAT(si.posting_date, '%%b') as month,
            SUM(sii.qty) as qty,
            SUM(sii.amount) as amount
        FROM `tabSales Invoice` si
        JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE si.docstatus = 1
            AND si.posting_date BETWEEN %s AND %s
        GROUP BY sii.item_code, DATE_FORMAT(si.posting_date, '%%b')
    """
    
    results = frappe.db.sql(query, (fy.year_start_date, fy.year_end_date), as_dict=True)
    
    actuals = []
    for row in results:
        actuals.append({
            "seed_variety": row.seed_variety,
            "month": row.month,
            "qty": row.qty,
            "amount": row.amount
        })
    
    # Make API call to parent
    import requests
    
    url = f"{settings.parent_site_url}/api/method/seed_core.api.sync.receive_subsidiary_actuals"
    headers = {
        "Authorization": f"token {settings.api_key}:{settings.get_password('api_secret')}",
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "subsidiary_code": settings.subsidiary_code,
            "fiscal_year": fiscal_year,
            "actuals": actuals
        }
    }
    
    try:
        import json
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if result.get("message", {}).get("success"):
            settings.last_sync_on = now_datetime()
            settings.save(ignore_permissions=True)
            frappe.db.commit()
        
        return result.get("message", {})
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


# ============================================
# VARIETY SYNC
# ============================================

@frappe.whitelist()
def get_varieties_for_subsidiary(subsidiary_code):
    """
    Called by subsidiary to fetch all seed varieties from parent.
    Returns varieties with commercial names.
    """
    settings = frappe.get_single("Seed Core Settings")
    
    if settings.site_type != "Parent Company":
        frappe.throw(_("This endpoint is only available on parent site"))
    
    varieties = frappe.get_all(
        "Seed Variety",
        fields=["name", "variety_name", "crop", "segment", "scientific_name", 
                "description", "image", "plant_characteristics", "fruit_characteristics",
                "resistance_codes", "cultivation_environment"]
    )
    
    result = []
    for v in varieties:
        # Get commercial names
        commercial_names = frappe.get_all(
            "Seed Variety Name",
            filters={"parent": v.name},
            fields=["country", "commercial_name"]
        )
        
        result.append({
            "variety_name": v.variety_name,
            "crop": v.crop,
            "segment": v.segment,
            "scientific_name": v.scientific_name,
            "description": v.description,
            "image": v.image,
            "plant_characteristics": v.plant_characteristics,
            "fruit_characteristics": v.fruit_characteristics,
            "resistance_codes": v.resistance_codes,
            "cultivation_environment": v.cultivation_environment,
            "commercial_names": commercial_names
        })
    
    return {"success": True, "varieties": result}


@frappe.whitelist()
def pull_varieties_from_parent():
    """
    Called on subsidiary to fetch seed varieties from parent site.
    Creates/updates local Seed Variety documents.
    """
    settings = frappe.get_single("Seed Core Settings")
    
    if settings.site_type != "Subsidiary":
        frappe.throw(_("This function is only for subsidiary sites"))
    
    if not settings.parent_site_url or not settings.api_key:
        frappe.throw(_("Parent site URL and API credentials not configured"))
    
    import requests
    
    url = f"{settings.parent_site_url}/api/method/seed_core.api.sync.get_varieties_for_subsidiary"
    headers = {
        "Authorization": f"token {settings.api_key}:{settings.get_password('api_secret')}"
    }
    params = {"subsidiary_code": settings.subsidiary_code}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        if not result.get("message", {}).get("success"):
            return {"success": False, "error": result.get("message", {}).get("error", "Unknown error")}
        
        varieties = result.get("message", {}).get("varieties", [])
        created = 0
        updated = 0
        
        for v_data in varieties:
            variety_name = v_data.get("variety_name")
            
            if frappe.db.exists("Seed Variety", variety_name):
                # Update existing
                doc = frappe.get_doc("Seed Variety", variety_name)
                
                # Only update if synced from parent (don't overwrite local edits on local varieties)
                if doc.is_synced_from_parent:
                    update_variety_from_parent(doc, v_data)
                    doc.last_synced_on = now_datetime()
                    doc.save(ignore_permissions=True)
                    updated += 1
            else:
                # Create new
                doc = frappe.new_doc("Seed Variety")
                doc.variety_name = variety_name
                update_variety_from_parent(doc, v_data)
                doc.is_synced_from_parent = 1
                doc.parent_variety_id = variety_name
                doc.last_synced_on = now_datetime()
                doc.insert(ignore_permissions=True)
                created += 1
        
        # Update last sync timestamp
        settings.last_sync_on = now_datetime()
        settings.save(ignore_permissions=True)
        frappe.db.commit()
        
        return {
            "success": True,
            "created": created,
            "updated": updated,
            "message": f"Synced {created + updated} varieties from parent"
        }
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def update_variety_from_parent(doc, data):
    """Update variety doc with data from parent"""
    doc.crop = data.get("crop")
    doc.segment = data.get("segment")
    doc.scientific_name = data.get("scientific_name")
    doc.description = data.get("description")
    doc.image = data.get("image")
    doc.plant_characteristics = data.get("plant_characteristics")
    doc.fruit_characteristics = data.get("fruit_characteristics")
    doc.resistance_codes = data.get("resistance_codes")
    doc.cultivation_environment = data.get("cultivation_environment")
    
    # Update commercial names
    doc.variety_names = []
    for cn in data.get("commercial_names", []):
        doc.append("variety_names", {
            "country": cn.get("country"),
            "commercial_name": cn.get("commercial_name")
        })


def get_country_for_subsidiary(subsidiary_code):
    """Map subsidiary code to country"""
    mapping = {
        "MA": "Morocco",
        "ES": "Spain",
        "TR": "Turkey"
    }
    return mapping.get(subsidiary_code)

