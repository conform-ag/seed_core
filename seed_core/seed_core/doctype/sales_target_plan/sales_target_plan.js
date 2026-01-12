frappe.ui.form.on('Sales Target Plan', {
    refresh: function (frm) {
        // Add button to fetch historical data
        if (!frm.doc.docstatus && frm.doc.party && frm.doc.fiscal_year) {
            frm.add_custom_button(__('Fetch Historical Data'), function () {
                frm.call('fetch_historical_data').then(() => {
                    frm.refresh_field('targets');
                    frm.dirty();
                });
            }, __('Actions'));
        }

        // Add button for parent company to pull subsidiary forecast
        if (!frm.doc.docstatus && frm.doc.target_level === 'Distributor/Subsidiary') {
            frm.add_custom_button(__('Pull Subsidiary Forecast'), function () {
                frappe.call({
                    method: 'seed_core.seed_core.doctype.sales_target_plan.sales_target_plan.get_subsidiary_forecast',
                    args: {
                        subsidiary: frm.doc.party,
                        fiscal_year: frm.doc.fiscal_year
                    },
                    callback: function (r) {
                        if (r.message && r.message.length) {
                            frm.clear_table('targets');
                            r.message.forEach(function (row) {
                                let child = frm.add_child('targets');
                                child.seed_variety = row.seed_variety;
                                child.month = row.month;
                                child.forecast_qty = row.forecast_qty;
                                child.forecast_amount = row.forecast_amount;
                            });
                            frm.refresh_field('targets');
                            frm.dirty();
                            frappe.msgprint(__('Loaded {0} rows from subsidiary forecast', [r.message.length]));
                        } else {
                            frappe.msgprint(__('No submitted forecast found for this subsidiary'));
                        }
                    }
                });
            }, __('Actions'));
        }
    },

    party: function (frm) {
        // Auto-fetch historical data when party is selected
        if (frm.doc.party && frm.doc.fiscal_year && frm.doc.company) {

            // Auto-fetch Price List for Distributor
            if (frm.doc.target_level === 'Distributor/Subsidiary' && frm.doc.party_type === 'Customer') {
                frappe.db.get_value('Customer', frm.doc.party, 'default_price_list')
                    .then(r => {
                        if (r && r.message && r.message.default_price_list) {
                            frm.set_value('price_list', r.message.default_price_list);
                        }
                    });
            }

            frm.call('fetch_historical_data').then(() => {
                frm.refresh_field('targets');
            });
        }
    },

    target_level: function (frm) {
        if (frm.doc.target_level === 'Country') {
            frm.set_value('party_type', 'Territory');
            // User must manually select Price List for Country as per requirement
        } else {
            frm.set_value('party_type', 'Customer');
        }
    },

    fiscal_year: function (frm) {
        // Auto-fetch when fiscal year changes
        if (frm.doc.party && frm.doc.fiscal_year && frm.doc.company) {
            frm.call('fetch_historical_data').then(() => {
                frm.refresh_field('targets');
            });
        }

        // Auto-set dates from fiscal year
        if (frm.doc.fiscal_year) {
            frappe.db.get_doc('Fiscal Year', frm.doc.fiscal_year).then(fy => {
                frm.set_value('from_date', fy.year_start_date);
                frm.set_value('to_date', fy.year_end_date);
            });
        }
    }
});

// Child table events
frappe.ui.form.on('Sales Target Item', {
    seed_variety: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.seed_variety) {

            // 1. Fetch Rate from Item Price (Item Code = Seed Variety Name)
            if (frm.doc.price_list) {
                frappe.call({
                    method: "frappe.client.get_value",
                    args: {
                        doctype: "Item Price",
                        filters: {
                            item_code: row.seed_variety,
                            price_list: frm.doc.price_list
                        },
                        fieldname: "price_list_rate"
                    },
                    callback: function (r) {
                        if (r.message) {
                            frappe.model.set_value(cdt, cdn, 'rate', r.message.price_list_rate);
                            calculate_row_amount(frm, cdt, cdn);
                        }
                    }
                });
            }

            // 2. Fetch Crop from Seed Variety
            frappe.db.get_value('Seed Variety', row.seed_variety, 'crop')
                .then(r => {
                    if (r && r.message && r.message.crop) {
                        frappe.model.set_value(cdt, cdn, 'crop', r.message.crop);
                    }
                });
        }
    },

    forecast_qty: function (frm, cdt, cdn) {
        calculate_row_amount(frm, cdt, cdn);
        calculate_row_delta(frm, cdt, cdn);
    },

    rate: function (frm, cdt, cdn) {
        calculate_row_amount(frm, cdt, cdn);
    },

    forecast_amount: function (frm, cdt, cdn) {
        calculate_totals(frm);
    }
});

function calculate_row_amount(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.forecast_qty && row.rate) {
        frappe.model.set_value(cdt, cdn, 'forecast_amount', row.forecast_qty * row.rate);
    }
    calculate_totals(frm); // Calculate totals after amount update
}

function calculate_row_delta(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.history_qty > 0) {
        row.delta_percent = ((row.forecast_qty - row.history_qty) / row.history_qty) * 100;
    } else {
        row.delta_percent = row.forecast_qty > 0 ? 100 : 0;
    }
    frm.refresh_field('targets');
}

function calculate_totals(frm) {
    let total_history_qty = 0;
    let total_history_amount = 0;
    let total_forecast_qty = 0;
    let total_forecast_amount = 0;

    frm.doc.targets.forEach(row => {
        total_history_qty += flt(row.history_qty);
        total_history_amount += flt(row.history_amount);
        total_forecast_qty += flt(row.forecast_qty);
        total_forecast_amount += flt(row.forecast_amount);
    });

    frm.set_value('total_history_qty', total_history_qty);
    frm.set_value('total_history_amount', total_history_amount);
    frm.set_value('total_forecast_qty', total_forecast_qty);
    frm.set_value('total_forecast_amount', total_forecast_amount);
}
