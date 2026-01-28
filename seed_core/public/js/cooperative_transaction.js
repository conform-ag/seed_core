
// Shared logic for Sales Invoice, Sales Order, Delivery Note
const cooperative_transaction_logic = {
    setup: function (frm) {
        frm.set_query("cooperative_member", function () {
            return {
                filters: {
                    cooperative: frm.doc.customer
                }
            };
        });
    },

    customer: function (frm) {
        if (frm.doc.customer) {
            frappe.db.get_value("Customer", frm.doc.customer, "is_cooperative")
                .then(r => {
                    if (r && r.message && r.message.is_cooperative) {
                        frm.set_df_property("cooperative_member", "hidden", 0);
                        frm.set_df_property("cooperative_member", "reqd", 1); // Maybe required? Lets keep optional for now unless requested.
                    } else {
                        frm.set_df_property("cooperative_member", "hidden", 1);
                        frm.set_value("cooperative_member", "");
                    }
                });
        } else {
            frm.set_df_property("cooperative_member", "hidden", 1);
            frm.set_value("cooperative_member", "");
        }
    }
};

frappe.ui.form.on("Sales Invoice", cooperative_transaction_logic);
frappe.ui.form.on("Sales Order", cooperative_transaction_logic);
frappe.ui.form.on("Delivery Note", cooperative_transaction_logic);
