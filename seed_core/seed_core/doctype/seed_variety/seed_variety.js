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

            // Load transaction and stock data
            load_stock_details(frm);
            load_sales_transactions(frm);
            load_purchase_transactions(frm);
        }
    },

    crop: function (frm) {
        if (frm.doc.segment) {
            frm.set_value('segment', '');
        }
    }
});

function load_stock_details(frm) {
    frappe.call({
        method: 'seed_core.seed_core.doctype.seed_variety.seed_variety.get_stock_details',
        args: { variety_name: frm.doc.name },
        callback: function (r) {
            if (r.message) {
                render_stock_details(frm, r.message);
            }
        }
    });
}

function render_stock_details(frm, data) {
    let html = '';

    if (data.length === 0) {
        html = '<div class="text-muted">No stock available</div>';
    } else {
        html = `
            <table class="table table-bordered table-sm">
                <thead>
                    <tr>
                        <th>Warehouse</th>
                        <th>Batch</th>
                        <th>Qty</th>
                        <th>UoM</th>
                        <th>Expiry</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.forEach(row => {
            html += `
                <tr>
                    <td><a href="/app/warehouse/${row.warehouse}">${row.warehouse}</a></td>
                    <td>${row.batch_no ? `<a href="/app/batch/${row.batch_no}">${row.batch_no}</a>` : '-'}</td>
                    <td style="text-align:right;font-weight:bold">${row.actual_qty}</td>
                    <td>${row.stock_uom || ''}</td>
                    <td>${row.expiry_date || '-'}</td>
                </tr>
            `;
        });

        html += '</tbody></table>';
    }

    frm.fields_dict.stock_detail_html.$wrapper.html(html);
}

function load_sales_transactions(frm) {
    frappe.call({
        method: 'seed_core.seed_core.doctype.seed_variety.seed_variety.get_sales_transactions',
        args: { variety_name: frm.doc.name },
        callback: function (r) {
            if (r.message) {
                render_sales_transactions(frm, r.message);
            }
        }
    });
}

function render_sales_transactions(frm, data) {
    let html = '';

    // Sales Orders
    html += '<h6>Sales Orders</h6>';
    if (data.sales_orders.length === 0) {
        html += '<div class="text-muted mb-3">No sales orders</div>';
    } else {
        html += render_transaction_table(data.sales_orders, 'sales-order');
    }

    // Sales Invoices
    html += '<h6>Sales Invoices</h6>';
    if (data.sales_invoices.length === 0) {
        html += '<div class="text-muted mb-3">No sales invoices</div>';
    } else {
        html += render_transaction_table(data.sales_invoices, 'sales-invoice');
    }

    // Delivery Notes
    html += '<h6>Delivery Notes</h6>';
    if (data.delivery_notes.length === 0) {
        html += '<div class="text-muted mb-3">No delivery notes</div>';
    } else {
        html += render_transaction_table(data.delivery_notes, 'delivery-note');
    }

    frm.fields_dict.sales_transactions_html.$wrapper.html(html);
}

function load_purchase_transactions(frm) {
    frappe.call({
        method: 'seed_core.seed_core.doctype.seed_variety.seed_variety.get_purchase_transactions',
        args: { variety_name: frm.doc.name },
        callback: function (r) {
            if (r.message) {
                render_purchase_transactions(frm, r.message);
            }
        }
    });
}

function render_purchase_transactions(frm, data) {
    let html = '';

    // Purchase Receipts
    html += '<h6>Purchase Receipts</h6>';
    if (data.purchase_receipts.length === 0) {
        html += '<div class="text-muted mb-3">No purchase receipts</div>';
    } else {
        html += render_transaction_table(data.purchase_receipts, 'purchase-receipt');
    }

    // Purchase Invoices
    html += '<h6>Purchase Invoices</h6>';
    if (data.purchase_invoices.length === 0) {
        html += '<div class="text-muted mb-3">No purchase invoices</div>';
    } else {
        html += render_transaction_table(data.purchase_invoices, 'purchase-invoice');
    }

    frm.fields_dict.purchase_transactions_html.$wrapper.html(html);
}

function render_transaction_table(data, doctype_slug) {
    let html = `
        <table class="table table-bordered table-sm mb-3">
            <thead>
                <tr>
                    <th>Document</th>
                    <th>Date</th>
                    <th>Party</th>
                    <th>Qty</th>
                    <th>Amount</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
    `;

    data.slice(0, 10).forEach(row => {
        let statusClass = '';
        if (row.status === 'Completed' || row.status === 'Paid') {
            statusClass = 'text-success';
        } else if (row.status === 'Overdue' || row.status === 'Cancelled') {
            statusClass = 'text-danger';
        }

        html += `
            <tr>
                <td><a href="/app/${doctype_slug}/${row.name}">${row.name}</a></td>
                <td>${row.date || ''}</td>
                <td>${row.party || ''}</td>
                <td style="text-align:right">${row.qty || 0}</td>
                <td style="text-align:right">${format_currency(row.amount || 0)}</td>
                <td class="${statusClass}">${row.status || ''}</td>
            </tr>
        `;
    });

    if (data.length > 10) {
        html += `<tr><td colspan="6" class="text-center text-muted">...and ${data.length - 10} more</td></tr>`;
    }

    html += '</tbody></table>';
    return html;
}
