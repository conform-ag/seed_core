frappe.ui.form.on("Seed Processing", {
    input_item: function (frm) {
        // Clear batch when item changes
        frm.set_value("input_batch", "");

        // Set filter for input_batch
        frm.set_query("input_batch", function () {
            return {
                filters: {
                    item: frm.doc.input_item
                }
            };
        });
    },

    input_batch: function (frm) {
        // Fetch and display batch details
        if (frm.doc.input_batch) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Batch",
                    name: frm.doc.input_batch
                },
                callback: function (r) {
                    if (r.message) {
                        var batch = r.message;
                        var html = `
							<div class="batch-info" style="padding: 10px; background: var(--bg-color); border-radius: 4px; margin-top: 10px;">
								<strong>Batch:</strong> ${batch.name}<br>
								<strong>Germination:</strong> ${batch.germination_percent || '-'}%<br>
								<strong>Purity:</strong> ${batch.purity_percent || '-'}%<br>
								<strong>Organic:</strong> ${batch.is_organic ? 'Yes' : 'No'}<br>
								<strong>Treated:</strong> ${batch.is_chemically_treated ? 'Yes' : 'No'}
							</div>
						`;
                        $(frm.fields_dict.input_batch_details.wrapper).html(html);
                    }
                }
            });
        } else {
            $(frm.fields_dict.input_batch_details.wrapper).html("");
        }
    },

    input_qty: function (frm) {
        frm.trigger("calculate_loss");
    },

    output_qty: function (frm) {
        frm.trigger("calculate_loss");
    },

    calculate_loss: function (frm) {
        if (frm.doc.input_qty && frm.doc.output_qty) {
            var waste = frm.doc.input_qty - frm.doc.output_qty;
            var loss = (waste / frm.doc.input_qty) * 100;
            frm.set_value("waste_qty", waste);
            frm.set_value("loss_percent", loss);
        }
    },

    refresh: function (frm) {
        // Set filter for input_batch on load
        if (frm.doc.input_item) {
            frm.set_query("input_batch", function () {
                return {
                    filters: {
                        item: frm.doc.input_item
                    }
                };
            });
        }

        // Show link to stock entry
        if (frm.doc.stock_entry && frm.doc.docstatus === 1) {
            frm.add_custom_button(__("View Stock Entry"), function () {
                frappe.set_route("Form", "Stock Entry", frm.doc.stock_entry);
            });
        }
    }
});
