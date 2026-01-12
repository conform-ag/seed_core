frappe.query_reports["Sales Target vs Reality"] = {
    "filters": [
        {
            "fieldname": "sales_target_plan",
            "label": __("Sales Target Plan"),
            "fieldtype": "Link",
            "options": "Sales Target Plan",
            "reqd": 1,
            "get_query": function () {
                return {
                    filters: {
                        "docstatus": 1
                    }
                };
            }
        }
    ]
};
