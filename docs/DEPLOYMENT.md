# Seed Core Multi-Site Deployment Guide

## Quick Start

### Installation (All Sites)

```bash
cd ~/frappe-bench
bench get-app --branch develop https://github.com/conform-ag/seed_core.git
bench --site [your-site] install-app seed_core
bench --site [your-site] migrate
bench build --app seed_core
sudo supervisorctl restart all
```

---

## Site Configuration

### Parent Site (Turkey)

1. Go to **Seed Core Settings**
2. Set **Site Type** = "Parent Company"
3. Save

### Subsidiary Site (Morocco/Spain)

1. Go to **Seed Core Settings**
2. Set:
   - **Site Type** = "Subsidiary"
   - **Subsidiary Code** = `MA` or `ES`
   - **Parent Site URL** = `https://erp.yukselseeds.com`
3. Configure API credentials (see below)
4. Save

---

## API Key Setup

### On Parent Site

1. Login as Administrator
2. **User** → Select admin user
3. Scroll to **API Access** → Click **Generate Keys**
4. Copy **API Key** and **API Secret**

> ⚠️ Save API Secret immediately - shown only once!

### On Subsidiary Site

1. **Seed Core Settings**
2. Paste API Key and API Secret
3. Click **Test Connection** to verify

---

## Sync Operations (Subsidiary)

From **Seed Core Settings** → **Actions**:

| Button | Purpose |
|--------|---------|
| **Sync Varieties** | Pull seed varieties from parent |
| **Sync Targets** | Pull sales target plans |
| **Push Actuals** | Send sales data to parent |

**Recommended Schedule:**
- Varieties: Weekly
- Targets: Monthly
- Actuals: Daily/Weekly

---

## Permissions (Subsidiary)

Configure in **Seed Core Settings → Subsidiary Permissions**:

| Setting | Default | Effect |
|---------|---------|--------|
| Can Edit Variety Descriptions | ❌ | Allow editing descriptions |
| Can Add Local Varieties | ❌ | Create own varieties |
| Can Edit Commercial Names | ✅ | Edit own country's names |

---

## Reports

| Report | Description |
|--------|-------------|
| Sales Target vs Reality | Target vs actual by variety/month |
| Consolidated Sales Dashboard | Group view with subsidiary filter |
| Regional Performance | By territory with manager |

---

## Update Procedure

```bash
bench update --apps seed_core
bench --site [your-site] migrate
bench build --app seed_core
sudo supervisorctl restart all
```

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| Connection failed | API credentials, parent URL |
| No varieties | Parent has varieties created |
| No targets | Fiscal year, territory mapping |
| Actuals not syncing | Sales Invoices submitted |
