frappe.ui.form.on('Seed Variety', {
    refresh: function (frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Sync Item'), function () {
                frm.call('sync_item');
            }, __('Actions'));
        }
    }
});
