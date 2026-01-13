frappe.query_reports["Consolidated Sales Dashboard"] = {
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
            "fieldname": "scope",
            "label": __("Scope"),
            "fieldtype": "Select",
            "options": "Local Only\nInclude Subsidiaries\nSubsidiaries Only",
            "default": "Include Subsidiaries"
        },
        {
            "fieldname": "subsidiary",
            "label": __("Subsidiary"),
            "fieldtype": "Select",
            "options": "\nMA - Morocco\nES - Spain\nAll Subsidiaries",
            "depends_on": "eval:doc.scope != 'Local Only'"
        },
        {
            "fieldname": "crop",
            "label": __("Seed Crop"),
            "fieldtype": "Link",
            "options": "Seed Crop"
        },
        {
            "fieldname": "territory",
            "label": __("Territory"),
            "fieldtype": "Link",
            "options": "Territory"
        }
    ],

    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        if (column.fieldname == "variance_pct") {
            if (data.variance_pct > 0) {
                value = "<span style='color:green;font-weight:bold'>▲ " + value + "</span>";
            } else if (data.variance_pct < 0) {
                value = "<span style='color:red;font-weight:bold'>▼ " + value + "</span>";
            }
        }

        if (column.fieldname == "achievement_pct") {
            if (data.achievement_pct >= 100) {
                value = "<span style='color:green;font-weight:bold'>" + value + "</span>";
            } else if (data.achievement_pct < 80) {
                value = "<span style='color:red;font-weight:bold'>" + value + "</span>";
            }
        }

        return value;
    }
};
