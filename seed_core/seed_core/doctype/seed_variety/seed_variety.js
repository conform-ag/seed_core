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
