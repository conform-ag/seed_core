frappe.ui.form.on('Seed Variety', {
    setup: function (frm) {
        frm.set_query('segment', function () {
            return {
                filters: {
                    crop: frm.doc.crop
                }
            };
        });
    },

    refresh: function (frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__('Sync Item'), function () {
                frm.call('sync_item');
            }, __('Actions'));
        }
    },

    crop: function (frm) {
        if (frm.doc.segment) {
            frm.set_value('segment', '');
        }
    }
});
