frappe.query_reports["Regional Performance"] = {
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
            "fieldname": "region",
            "label": __("Region"),
            "fieldtype": "Select",
            "options": "\nEurope\nMaghreb/Africa\nLATAM\nUSA/Canada\nAsia"
        },
        {
            "fieldname": "territory",
            "label": __("Territory"),
            "fieldtype": "Link",
            "options": "Territory"
        },
        {
            "fieldname": "crop",
            "label": __("Seed Crop"),
            "fieldtype": "Link",
            "options": "Seed Crop"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname == "achievement_pct") {
            if (data.achievement_pct >= 100) {
                value = "<span style='color:green;font-weight:bold'>✓ " + value + "</span>";
            } else if (data.achievement_pct < 80) {
                value = "<span style='color:red;font-weight:bold'>✗ " + value + "</span>";
            }
        }

        return value;
    }
};
