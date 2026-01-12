frappe.query_reports["Sales Target vs Reality"] = {
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
            "default": frappe.defaults.get_user_default("Fiscal Year"),
            "reqd": 1
        },
        {
            "fieldname": "country",
            "label": __("Country"),
            "fieldtype": "Link",
            "options": "Territory"
        },
        {
            "fieldname": "customer",
            "label": __("Distributor/Subsidiary"),
            "fieldtype": "Link",
            "options": "Customer"
        },
        {
            "fieldname": "crop",
            "label": __("See Crop"),
            "fieldtype": "Link",
            "options": "Seed Crop"
        },
        {
            "fieldname": "seed_variety",
            "label": __("Seed Variety"),
            "fieldtype": "Link",
            "options": "Seed Variety",
            "get_query": function () {
                var crop = frappe.query_report.get_filter_value("crop");
                if (crop) {
                    return {
                        filters: {
                            "crop": crop
                        }
                    };
                }
            }
        }
    ]
};
