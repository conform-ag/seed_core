// Copyright (c) 2024, Conform and contributors
// For license information, please see license.txt

frappe.ui.form.on('Seed Core Settings', {
    refresh: function (frm) {
        // Subsidiary site actions
        if (frm.doc.site_type === 'Subsidiary' && frm.doc.parent_site_url) {
            frm.add_custom_button(__('Test Connection'), function () {
                frappe.call({
                    method: 'seed_core.api.sync.test_parent_connection',
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__('Connection successful!'), __('Success'));
                        } else {
                            frappe.msgprint(__('Connection failed: ' + (r.message?.error || 'Unknown error')), __('Error'));
                        }
                    }
                });
            });

            frm.add_custom_button(__('Pull Targets from Parent'), function () {
                frappe.call({
                    method: 'seed_core.api.sync.pull_targets_from_parent',
                    freeze: true,
                    freeze_message: __('Syncing targets from parent...'),
                    callback: function (r) {
                        if (r.message) {
                            if (r.message.success) {
                                frappe.msgprint({
                                    title: __('Sync Complete'),
                                    message: r.message.message,
                                    indicator: 'green'
                                });
                            } else {
                                frappe.msgprint({
                                    title: __('Sync Failed'),
                                    message: r.message.error,
                                    indicator: 'red'
                                });
                            }
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Actions'));

            frm.add_custom_button(__('Push Actuals to Parent'), function () {
                frappe.call({
                    method: 'seed_core.api.sync.push_actuals_to_parent',
                    freeze: true,
                    freeze_message: __('Pushing sales data to parent...'),
                    callback: function (r) {
                        if (r.message) {
                            if (r.message.success) {
                                frappe.msgprint({
                                    title: __('Sync Complete'),
                                    message: r.message.message,
                                    indicator: 'green'
                                });
                            } else {
                                frappe.msgprint({
                                    title: __('Sync Failed'),
                                    message: r.message.error,
                                    indicator: 'red'
                                });
                            }
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Actions'));
        }

        // Show last sync info
        if (frm.doc.last_sync_on) {
            frm.dashboard.add_indicator(
                __('Last Sync: {0}', [frappe.datetime.prettyDate(frm.doc.last_sync_on)]),
                'blue'
            );
        }
    }
});
