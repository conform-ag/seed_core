frappe.listview_settings["Seed Variety"] = {
    hide_name_column: true, // Attempt to hide ID column if supported by version
    onload: function (listview) {
        listview.page.add_inner_button(__("Refresh Names"), function () {
            frappe.confirm(__("This will update all variety names based on their default commercial name. Continue?"), function () {
                frappe.call({
                    method: "seed_core.seed_core.doctype.seed_variety.seed_variety.update_condensed_names",
                    freeze: true,
                    callback: function (r) {
                        if (!r.exc) {
                            frappe.msgprint(__("Variety names updated."));
                            listview.refresh();
                        }
                    }
                });
            });
        });
    });
});

listview.page.add_actions_menu_item(__("Sync to Items"), function () {
    const checked_items = listview.get_checked_items();
    if (checked_items.length === 0) {
        frappe.msgprint(__("Please select varieties to sync."));
        return;
    }

    const names = checked_items.map(item => item.name);
    frappe.call({
        method: "seed_core.seed_core.doctype.seed_variety.seed_variety.sync_selected_to_items",
        args: { names: names },
        freeze: true,
        callback: function (r) {
            if (!r.exc) {
                listview.clear_checked_items();
                listview.refresh();
            }
        }
    });
});
    }
};
