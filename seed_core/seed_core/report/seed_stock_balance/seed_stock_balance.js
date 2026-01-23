frappe.query_reports["Seed Stock Balance"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company")
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse"
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
            "fieldname": "variety",
            "label": __("Variety"),
            "fieldtype": "Link",
            "options": "Seed Variety"
        },
        {
            "fieldname": "show_organic_only",
            "label": __("Organic Only"),
            "fieldtype": "Check"
        },
        {
            "fieldname": "show_untreated_only",
            "label": __("Untreated Only"),
            "fieldtype": "Check"
        },
        {
            "fieldname": "show_retest_due",
            "label": __("Retest Due Only"),
            "fieldtype": "Check"
        }
    ],
    "formatter": function (value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);

        // Highlight retest due batches
        if (column.fieldname === "status") {
            if (data.status === "Retest Due") {
                value = "<span style='color: red; font-weight: bold;'>" + value + "</span>";
            } else if (data.status === "Retest Soon") {
                value = "<span style='color: orange;'>" + value + "</span>";
            } else if (data.status === "OK") {
                value = "<span style='color: green;'>" + value + "</span>";
            }
        }

        return value;
    }
};
