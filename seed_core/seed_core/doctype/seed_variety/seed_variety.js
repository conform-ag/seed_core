frappe.ui.form.on('Seed Variety', {
    refresh: function (frm) {
        // Filter Segment based on Crop
        frm.set_query('segment', function () {
            return {
                filters: {
                    crop: frm.doc.crop
                }
            };
        });
    },

    crop: function (frm) {
        // Clear segment if crop changes
        frm.set_value('segment', '');
    }
});
