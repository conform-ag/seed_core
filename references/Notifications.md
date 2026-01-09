
Yuksel Seeds – Complete ERPNext Notifications Strategy

1. SALES MODULE

1.1 Sales Order Creation
Trigger: Sales Order submitted
Condition: docstatus = 1
Recipients: Sales Manager, Area Manager of region, Logistics
Purpose: Immediate visibility of new orders

1.2 Sales Order Approval
Trigger: Workflow state = “Pending Approval”
Recipients: Approver (Sales Director, Finance depending on workflow)
Purpose: Faster approval cycle

1.3 Delayed Sales Orders
Trigger: Daily scheduler
Condition: Delivery date < today AND % delivered < 100%
Recipients: Sales Manager, Logistics
Purpose: Follow-up on overdue deliveries

1.4 Sales Order on Hold / Stopped
Trigger: Status changed
Recipients: Sales Director, Finance, Logistics
Purpose: Ensure alignment when orders are blocked

2. PURCHASE MODULE

2.1 New Purchase Order
Trigger: PO submitted
Recipients: Procurement manager, Finance
Purpose: Immediate tracking of supplier commitments

2.2 PO Approval Pending > 48h
Trigger: Scheduled daily check
Recipients: Relevant approver
Purpose: Avoid bottlenecks in procurement

2.3 Delivery Date Approaching
Trigger: 3 days before expected delivery
Recipients: Logistics, Procurement
Purpose: Ensure supplier delivery control

3. STOCK / INVENTORY MODULE

3.1 Low Stock Alert
Trigger: Stock ledger update
Condition: Actual Qty < Reorder Level
Recipients: Stock Manager, Logistics, Area Manager
Purpose: Prevent stock-out of key varieties

3.2 Negative Stock Alert
Trigger: Stock entry or SO
Recipients: Stock Manager, Finance
Purpose: Prevent accounting inconsistencies

3.3 Material Transfer Submitted
Trigger: Stock Entry submitted
Recipients: Logistics
Purpose: Track internal movements between warehouses/subsidiaries

3.4 Seed Batch Expiry Alert
Trigger: Scheduled weekly
Condition: Batch expiry within 90 days
Recipients: Logistics, Sales, Country Manager
Purpose: Manage seed viability and avoid expiry losses

4. ACCOUNTING & FINANCE MODULE

4.1 New Sales Invoice
Trigger: Invoice submitted
Recipients: Finance, Sales
Purpose: Follow up payments & revenue recognition

4.2 Overdue Invoices
Trigger: Daily
Condition: Outstanding > 0 AND due_date < today
Recipients: Finance, Sales Manager
Purpose: Better receivables management

4.3 Payment Entry Cancelled
Trigger: Cancellation
Recipients: Finance manager
Purpose: Control accounting revisions

5. CRM MODULE

5.1 New Lead
Trigger: Lead created
Recipients: Country Manager / Area Manager
Purpose: Quick follow-up

5.2 Lead Not Updated (7 Days)
Trigger: Scheduled check
Recipients: Assigned Salesperson, Area Manager
Purpose: Improve CRM discipline

5.3 Opportunity Approaching Expected Close Date
Trigger: 3 days before
Recipients: Sales manager
Purpose: Accuracy on sales forecasting

6. QUALITY CONTROL MODULE

6.1 Germination Result Available
Trigger: QC Test completed
Recipients: Stock manager, Sales, Product development
Purpose: Speed up batch release decisions

6.2 QC Test Failure
Trigger: Germination < standard / disease presence
Recipients: QA manager, Stock manager, Sales director
Purpose: Rapid reaction to quality risks

7. HR / WORKFLOWS

7.1 Leave Application Submitted
Trigger: New leave request
Recipients: Manager of the employee
Purpose: Fast approval

7.2 Expense Claim Submitted
Trigger: Expense claim submitted
Recipients: Accounting manager
Purpose: Quick reimbursement management

7.3 Employee Evaluation Reminder
Trigger: Monthly
Recipients: Managers
Purpose: Track employee performance cycle

8. SYSTEM ADMINISTRATION & CONTROL

8.1 Login Attempt Failure (Security Alert)
Trigger: 5 failed attempts
Recipients: IT Manager (Hicham), System Admin
Purpose: Improve system security

8.2 Backup Success / Failure
Trigger: After scheduled backup
Recipients: IT Manager
Purpose: Verify backup health

9. YUKSEL SEEDS CUSTOM NOTIFICATIONS

9.3 Regional Sales Notifications
- Europe → Notify Nico
- Maghreb / Africa → Notify Nassir
- Poland → Notify Oskar
- Netherlands → Notify Nico
- Mexico / LATAM → Notify Miguel
- USA / Canada → Notify Hicham & colleagues

9.4 Seeds With Critical Commercial Importance
Create specific alerts for:
- Sweetloom
- Toptoma & Round Tomato lines
- Kapia (Princessa, Baronessa, Duchessa)
- Mini cucumbers (One-bite / Two-bite)

Trigger: low stock, order > forecast, or batch expiry soon.

