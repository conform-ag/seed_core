# Seed Core - ERPNext Custom App for Seed Companies

## Overview

**Seed Core** is a custom Frappe/ERPNext application designed specifically for seed companies. It extends ERPNext's functionality to manage seed varieties, crops, sales target planning, and performance tracking across multiple subsidiaries and countries.

---

## Key Features

### 1. Seed Variety Management
- **Seed Variety DocType**: Manages seed varieties with detailed characteristics (plant, fruit, resistances)
- **Seed Crop DocType**: Categorizes varieties by crop type (Tomato, Cucumber, Pepper, etc.)
- **Auto Item Creation**: Each Seed Variety automatically creates a corresponding ERPNext Item for stock and pricing
- **Image Sync**: Images attached to Seed Variety sync to the linked Item

### 2. Sales Target Planning
- **Sales Target Plan**: Create annual sales targets by Distributor/Subsidiary or Country
- **Monthly Breakdown**: Set target quantities for each Seed Variety by month
- **Historical Data**: Pull previous year's sales data as baseline
- **Price List Integration**: Auto-fetch rates from distributor's price list
- **Crop-Based Filtering**: Filter seed varieties by crop when adding targets

### 3. Sales Target vs Reality Report
- **Detailed Breakdown**: View targets by Crop, Variety, Party, and Month
- **Qty & Amount Tracking**: Track both quantities and monetary values
- **Variance Analysis**: See variance (qty and %) between target and actual
- **Aggregated Charts**: Bar chart showing Target Qty vs Actual Qty by month
- **Multi-Plan Aggregation**: Aggregate data across multiple plans (by Company, Fiscal Year, Country)

### 4. Workspace Dashboard
- **KPI Cards**: Total Seed Varieties, Total Distributors
- **Quick Access**: Shortcuts to key DocTypes and Reports
- **Visual Overview**: Dashboard chart showing target vs reality

---

## DocTypes

| DocType | Purpose |
|---------|---------|
| **Seed Crop** | Categories for seed types (Tomato, Cucumber, etc.) |
| **Seed Variety** | Individual seed varieties with characteristics |
| **Sales Target Plan** | Annual sales target document |
| **Sales Target Item** | Child table for monthly targets per variety |

---

## Reports

| Report | Description |
|--------|-------------|
| **Sales Target vs Reality** | Compare targets against actual sales from invoices |

---

## Architecture

```
seed_core/
├── doctype/
│   ├── seed_crop/           # Crop categories
│   ├── seed_variety/        # Seed varieties with auto-item creation
│   ├── sales_target_plan/   # Main planning document
│   └── sales_target_item/   # Monthly target rows
├── report/
│   └── sales_target_vs_reality/  # Performance report
├── workspace/
│   └── seed_core/           # App dashboard
├── print_format/
│   ├── sales_target_plan_classic/
│   └── sales_target_vs_reality_print/
├── number_card/
│   ├── total_seed_varieties/
│   └── total_distributors/
└── dashboard_chart/
    └── target_vs_reality_overview/
```

---

## Workflow

### Creating a Sales Target Plan

1. **Create New Plan**: Go to Sales Target Plan → New
2. **Select Scope**: Choose Company, Fiscal Year, and Target Level (Distributor/Country)
3. **Select Party**: Choose the Distributor or Territory
4. **Load History** (Optional): Click "Load Historical Data" to pull previous year's sales
5. **Add Targets**: Add rows with Crop, Seed Variety, Month, and Target Qty
6. **Submit**: Submit the plan to finalize

### Table Structure
Each row in the targets table:
- **Crop**: Filter for seed variety
- **Seed Variety**: The variety to target
- **Month**: Target month (Jan-Dec)
- **Target Qty**: Quantity to sell

### Viewing Performance
1. Go to **Sales Target vs Reality** report
2. Select filters (Company, Fiscal Year, Country/Customer)
3. View detailed breakdown by Crop/Variety/Party/Month
4. Check variance (qty and %) against targets

---

## Integration Points

- **Price Lists**: Fetches rates from ERPNext Price Lists
- **Sales Invoices**: Pulls actual sales from submitted invoices
- **Territories**: Uses ERPNext Territory hierarchy for country-based aggregation
- **Items**: Seed Varieties create Items for stock tracking
- **Customers**: Links to ERPNext Customer for distributor management

---

## Installation

```bash
# Get the app
bench get-app --branch develop https://github.com/conform-ag/seed_core.git

# Install on site
bench --site [sitename] install-app seed_core

# Run migrations
bench --site [sitename] migrate

# Build assets
bench build --app seed_core
```

---

## Configuration

1. **Create Seed Crops**: Setup → Seed Crop → Add crops (Tomato, Cucumber, etc.)
2. **Import Seed Varieties**: Import or create varieties linked to crops
3. **Setup Price Lists**: Assign price lists to customers with variety pricing
4. **Create Fiscal Years**: Ensure fiscal years are setup in ERPNext

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-12 | 1.0.0 | Initial release with Sales Target Plan and Report |

---

## Support

For issues and feature requests, contact the development team or create an issue in the repository.
