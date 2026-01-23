frappe.ui.form.on("Sales Target Plan", {
    refresh: function (frm) {
        if (!frm.is_new()) {
            // Calculate Actuals button
            frm.add_custom_button(__("Calculate Actuals"), function () {
                frm.call({
                    doc: frm.doc,
                    method: "calculate_actuals",
                    callback: function (r) {
                        frm.reload_doc();
                    }
                });
            }, __("Actions"));

            // Consolidate Forecasts button
            frm.add_custom_button(__("Consolidate Forecasts"), function () {
                // Show dialog to select forecasts
                let d = new frappe.ui.form.MultiSelectDialog({
                    doctype: "Sales Forecast",
                    target: frm,
                    setters: {
                        fiscal_year: frm.doc.fiscal_year
                    },
                    get_query() {
                        return {
                            filters: {
                                docstatus: 1,
                                fiscal_year: frm.doc.fiscal_year
                            }
                        };
                    },
                    action(selections) {
                        if (selections.length > 0) {
                            frm.call({
                                doc: frm.doc,
                                method: "consolidate_forecasts",
                                args: {
                                    forecast_names: selections
                                },
                                callback: function (r) {
                                    frm.reload_doc();
                                }
                            });
                        }
                        d.dialog.hide();
                    }
                });
            }, __("Actions"));
        }

        // Show progress dashboard
        if (frm.doc.total_target_amount && frm.doc.total_target_amount > 0) {
            let percent = (frm.doc.total_actual_amount / frm.doc.total_target_amount) * 100;
            let color = percent >= 100 ? "green" : (percent >= 75 ? "blue" : (percent >= 50 ? "orange" : "red"));

            frm.dashboard.add_indicator(
                __("Achievement: {0}%", [percent.toFixed(1)]),
                color
            );
        }
    },

    target_for: function (frm) {
        frm.set_value("target_entity", "");
    }
});
