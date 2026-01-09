frappe.ui.form.on('Sales Target Plan', {
    refresh: function(frm) {
        // Add button to fetch historical data
        if (!frm.doc.docstatus && frm.doc.party && frm.doc.fiscal_year) {
            frm.add_custom_button(__('Fetch Historical Data'), function() {
                frm.call('fetch_historical_data').then(() => {
                    frm.refresh_field('targets');
                    frm.dirty();
                });
            }, __('Actions'));
        }
        
        // Add button for parent company to pull subsidiary forecast
        if (!frm.doc.docstatus && frm.doc.target_level === 'Distributor/Subsidiary') {
            frm.add_custom_button(__('Pull Subsidiary Forecast'), function() {
                frappe.call({
                    method: 'seed_core.seed_core.doctype.sales_target_plan.sales_target_plan.get_subsidiary_forecast',
                    args: {
                        subsidiary: frm.doc.party,
                        fiscal_year: frm.doc.fiscal_year
                    },
                    callback: function(r) {
                        if (r.message && r.message.length) {
                            frm.clear_table('targets');
                            r.message.forEach(function(row) {
                                let child = frm.add_child('targets');
                                child.item_code = row.item_code;
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
    
    party: function(frm) {
        // Auto-fetch historical data when party is selected
        if (frm.doc.party && frm.doc.fiscal_year && frm.doc.company) {
            frm.call('fetch_historical_data').then(() => {
                frm.refresh_field('targets');
            });
        }
    },
    
    fiscal_year: function(frm) {
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

// Child table events for real-time delta calculation
frappe.ui.form.on('Sales Target Item', {
    forecast_qty: function(frm, cdt, cdn) {
        calculate_row_delta(frm, cdt, cdn);
    },
    
    forecast_amount: function(frm, cdt, cdn) {
        calculate_totals(frm);
    }
});

function calculate_row_delta(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    if (row.history_qty > 0) {
        row.delta_percent = ((row.forecast_qty - row.history_qty) / row.history_qty) * 100;
    } else {
        row.delta_percent = row.forecast_qty > 0 ? 100 : 0;
    }
    frm.refresh_field('targets');
    calculate_totals(frm);
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
