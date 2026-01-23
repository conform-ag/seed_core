frappe.ui.form.on("Sales Forecast", {
    refresh: function (frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Fetch Last Year Actuals"), function () {
                frm.call({
                    doc: frm.doc,
                    method: "fetch_last_year_actuals",
                    callback: function (r) {
                        frm.reload_doc();
                    }
                });
            }, __("Actions"));
        }
    }
});

frappe.ui.form.on("Forecast Item", {
    suggested_qty: function (frm, cdt, cdn) {
        calculate_expected_amount(frm, cdt, cdn);
    },

    suggested_price: function (frm, cdt, cdn) {
        calculate_expected_amount(frm, cdt, cdn);
    }
});

function calculate_expected_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.expected_amount = flt(row.suggested_qty) * flt(row.suggested_price);
    frm.refresh_field("forecast_items");

    // Recalculate totals
    let total_qty = 0;
    let total_amount = 0;
    frm.doc.forecast_items.forEach(function (item) {
        total_qty += flt(item.suggested_qty);
        total_amount += flt(item.expected_amount);
    });
    frm.set_value("total_suggested_qty", total_qty);
    frm.set_value("total_expected_amount", total_amount);
}
