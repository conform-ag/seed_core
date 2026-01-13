// Copyright (c) 2024, Conform and contributors
// For license information, please see license.txt

frappe.ui.form.on('Seed Core Settings', {
    refresh: function (frm) {
        if (frm.doc.site_type === 'Subsidiary' && frm.doc.parent_site_url) {
            frm.add_custom_button(__('Test Connection'), function () {
                frappe.call({
                    method: 'seed_core.seed_core.doctype.seed_core_settings.seed_core_settings.test_parent_connection',
                    callback: function (r) {
                        if (r.message && r.message.success) {
                            frappe.msgprint(__('Connection successful!'), __('Success'));
                        } else {
                            frappe.msgprint(__('Connection failed: ' + (r.message.error || 'Unknown error')), __('Error'));
                        }
                    }
                });
            });

            frm.add_custom_button(__('Sync Master Data'), function () {
                frappe.call({
                    method: 'seed_core.seed_core.doctype.seed_core_settings.seed_core_settings.sync_master_data',
                    callback: function (r) {
                        if (r.message) {
                            frappe.msgprint(r.message);
                            frm.reload_doc();
                        }
                    }
                });
            }, __('Actions'));
        }
    }
});
