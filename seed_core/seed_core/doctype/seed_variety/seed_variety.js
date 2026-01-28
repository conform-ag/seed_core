frappe.ui.form.on("Seed Variety", {
    seed_crop: function (frm) {
        // Filter segments by selected crop
        frm.set_query("seed_segment", function () {
            return {
                filters: {
                    seed_crop: frm.doc.seed_crop
                }
            };
        });
        // Clear segment and subsegment when crop changes
        frm.set_value("seed_segment", "");
        frm.set_value("seed_subsegment", "");
    },

    seed_segment: function (frm) {
        // Filter subsegments by selected segment
        frm.set_query("seed_subsegment", function () {
            return {
                filters: {
                    seed_segment: frm.doc.seed_segment
                }
            };
        });
        // Clear subsegment when segment changes
        frm.set_value("seed_subsegment", "");
    },

    refresh: function (frm) {
        // Add button to manually sync to Item
        if (!frm.is_new() && frm.doc.linked_item) {
            frm.add_custom_button(__("View Linked Item"), function () {
                frappe.set_route("Form", "Item", frm.doc.linked_item);
            }, __("Actions"));
        }

        if (!frm.is_new()) {
            frm.add_custom_button(__("Sync to Item"), function () {
                frm.call({
                    doc: frm.doc,
                    method: "sync_to_item",
                    callback: function (r) {
                        frm.reload_doc();
                    }
                });
            }, __("Actions"));
        }
    }
});

frappe.ui.form.on("Variety Commercial Name", {
    is_default: function (frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        if (row.is_default) {
            // Uncheck other rows
            frm.doc.commercial_names.forEach(function (d) {
                if (d.name !== row.name) {
                    frappe.model.set_value(d.doctype, d.name, "is_default", 0);
                }
            });
            // Update default commercial name field
            frm.set_value("default_commercial_name", row.commercial_name);
        } else {
            // If unchecked, and it was the value in default field, ignore clear for now, 
            // let serve side handle or user pick another. 
            // Actually, if unchecking the only default, clear the field.
            if (frm.doc.default_commercial_name === row.commercial_name) {
                frm.set_value("default_commercial_name", "");
            }
        }
    },
    commercial_names_remove: function (frm) {
        // Recalculate default if row removed
        let found = false;
        frm.doc.commercial_names.forEach(function (d) {
            if (d.is_default) {
                frm.set_value("default_commercial_name", d.commercial_name);
                found = true;
            }
        });
        if (!found) frm.set_value("default_commercial_name", "");
    }
});
