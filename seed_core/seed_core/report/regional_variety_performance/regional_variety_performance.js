frappe.query_reports["Regional Variety Performance"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "fiscal_year",
            "label": __("Fiscal Year"),
            "fieldtype": "Link",
            "options": "Fiscal Year",
            "default": frappe.defaults.get_user_default("fiscal_year"),
            "reqd": 1
        },
        {
            "fieldname": "territory",
            "label": __("Territory"),
            "fieldtype": "Link",
            "options": "Territory"
        },
        {
            "fieldname": "crop",
            "label": __("Crop"),
            "fieldtype": "Link",
            "options": "Seed Crop"
        },
        {
            "fieldname": "segment",
            "label": __("Segment"),
            "fieldtype": "Link",
            "options": "Seed Segment",
            "get_query": function () {
                var crop = frappe.query_report.get_filter_value("crop");
                if (crop) {
                    return {
                        filters: { seed_crop: crop }
                    };
                }
            }
        },
        {
            "fieldname": "lifecycle_stage",
            "label": __("Lifecycle Stage"),
            "fieldtype": "Select",
            "options": "\nR&D\nTrial\nCommercial\nPhase Out\nDropped"
        }
    ]
};
