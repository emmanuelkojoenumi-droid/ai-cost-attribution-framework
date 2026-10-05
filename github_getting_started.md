# Getting Started: AI Cost Attribution Framework

This guide walks you through implementing the AI-Assisted Cost Attribution Framework in your organization — from initial assessment through full deployment.

---

## Prerequisites

Before starting, confirm you have:

- [ ] Access to your organization's cost data by category or cost pool
- [ ] Operational metrics data for your primary product lines or business units (user counts, transaction volumes, unit volumes, or headcount)
- [ ] Python 3.8+ installed (for the analytical scripts)
- [ ] A spreadsheet tool (Excel or Google Sheets) or a BI platform (Tableau, Power BI, Apache Superset, Amazon QuickSight)

**You do not need:** proprietary software, enterprise licenses, or dedicated data engineering resources. This framework is intentionally designed for organizations with standard data infrastructure.

---

## Step 1: Assess Your Current State

Before designing your new attribution methodology, understand what you are working with.

### 1.1 Audit Your Current Allocation Method

Answer these questions about your current approach:

**What drivers are you currently using?**
- Headcount only → high misattribution risk
- Revenue percentage → misattributes unless costs scale with revenue
- Square footage → only appropriate for physical space costs
- Equal split → almost always incorrect in complex environments
- Consumption-based → you may already have a strong foundation

**When was your current methodology last reviewed?**
- Less than 12 months → likely current
- 1-3 years → likely partially outdated
- More than 3 years → significant misattribution risk

**What is the magnitude of shared costs you are attributing?**
- < $1M annually → lighter methodology may be sufficient
- $1M-$50M → usage-based methodology will produce material improvement
- > $50M → usage-based methodology is essential; misattribution risk is significant

### 1.2 Identify Your Cost Pools

List all shared cost categories that require allocation across product lines or business units. For each cost pool, note:

```
Cost Pool Name: _______________
Annual Amount ($): _______________
Current Allocation Driver: _______________
Suspected Accuracy: High / Medium / Low
Available Consumption Data: Yes / No
```

### 1.3 Gather Driver Data

For each potential allocation driver, assess data availability:

| Driver | Data Source | Frequency | Confidence |
|---|---|---|---|
| Monthly Active Users | Product analytics | Monthly | High / Medium / Low |
| Monthly Active Devices | Device telemetry | Monthly | High / Medium / Low |
| Transaction volume | Transaction logs | Monthly | High / Medium / Low |
| Unit volume | Supply chain system | Monthly | High / Medium / Low |
| Headcount | HR system | Monthly | High / Medium / Low |
| Direct consumption | Infrastructure billing | Monthly | High / Medium / Low |

---

## Step 2: Design Your Attribution Architecture

### 2.1 Map Cost Pools to Drivers

Using the driver selection guidance in [methodology.md](methodology.md), create your mapping table:

```
| Cost Pool | Annual Amount | Primary Driver | Rationale |
|---|---|---|---|
| [Cost pool 1] | $___M | [Driver] | [Why this driver] |
| [Cost pool 2] | $___M | [Driver] | [Why this driver] |
```

**Decision rules:**
- If direct consumption data is available → use it
- If no consumption data exists but the cost scales with users → use MAU/MAD
- If the cost scales with processing volume → use TPS
- If the cost scales with physical units → use unit volume
- If no consumption metric applies → use headcount as driver of last resort

### 2.2 Validate Your Driver Data

Before building the allocation model, validate the driver data you have gathered:

```python
# Use the scaling_drivers.py utility to validate driver data completeness
from src.scaling_drivers import validate_driver_data

drivers = {
    'MAU': {'Product_A': 71.0, 'Product_B': 2.0, 'Product_C': 17.7},
    'Units': {'Product_A': 25.3, 'Product_B': 0.7, 'Product_C': 12.4},
}

validation_results = validate_driver_data(drivers)
print(validation_results)
```

Check for:
- Missing values (product lines with no driver data)
- Zero values (product lines with zero consumption — verify this is correct)
- Implausible values (outliers that may indicate data errors)

### 2.3 Build Your Allocation Model

**Option A: Excel/Sheets Implementation**

The simplest implementation uses a structured spreadsheet:

1. **Input tab**: Driver data by product line and month
2. **Mapping tab**: Cost pool to driver mapping table
3. **Allocation tab**: XLOOKUP or INDEX/MATCH formulas linking inputs to allocations
4. **Output tab**: Allocated costs by product line and cost pool
5. **Validation tab**: Automated checks confirming allocations sum correctly

Key formula pattern (Excel XLOOKUP):
```excel
=XLOOKUP([ServiceName], [InputFile]![LookupRange], [InputFile]![ValueRange])
```

**Option B: Python Implementation**

For larger or more complex cost environments:

```python
from src.cost_attribution import CostAttributionModel

# Initialize with your cost pools and driver data
model = CostAttributionModel(
    cost_pools=cost_pools_df,      # DataFrame: cost pool | amount | driver
    driver_data=driver_data_df,    # DataFrame: product line | driver | value
    period='2026-Q2'
)

# Run attribution
results = model.run_attribution()

# Validate results
validation = model.validate(results)
print(validation.summary())

# Export
results.to_csv('output/allocated_costs_2026_Q2.csv', index=False)
```

---

## Step 3: Validate Before Deploying

Run all validation checks before using the new allocation in any financial reporting.

### 3.1 Completeness Check

```python
from src.validation import run_validation_suite

validation = run_validation_suite(
    allocated_costs=results,
    total_cost_budget=total_spend,
    prior_period=prior_period_results
)

# All checks should pass before proceeding
assert validation.completeness_check == 'PASS'
assert validation.sum_check == 'PASS'
assert validation.prior_period_variance < 0.30  # flag if > 30% change
```

### 3.2 Reasonableness Check

For each product line, verify the allocated cost is directionally consistent with its operational footprint:

- Product lines with higher user counts → higher user-facing infrastructure costs
- Product lines with higher transaction volumes → higher processing infrastructure costs
- Product lines with more physical units → higher supply chain costs

If any product line's allocated cost seems inconsistent with its operational activity, investigate the driver data for that product line before proceeding.

### 3.3 Prior Period Comparison

Compare your new allocation to the prior period. Document:
- Which product lines saw cost increases (and why)
- Which product lines saw cost decreases (and why)
- Which changes reflect methodology correction vs. genuine operational changes

This documentation is important for stakeholder communication.

---

## Step 4: Build the Analytics Layer

Once attribution is accurate, make it accessible.

### 4.1 Connect to Your BI Tool

The output CSV from the attribution model connects directly to standard BI tools:

**Apache Superset (open source):**
```bash
# Install Superset
pip install apache-superset

# Initialize and start
superset init
superset run -p 8088
```

**Amazon QuickSight:**
Upload the output CSV as a SPICE dataset, then build calculated fields for variance analysis.

**Tableau / Power BI:**
Connect directly to the output CSV or database table.

### 4.2 Core Calculated Fields

Build these calculated fields in your BI tool:

```
# Variance to baseline
Variance = Actuals - Baseline

# Variance percentage
Variance_Pct = (Actuals - Baseline) / Baseline

# Year-over-year change
YoY_Change = (Current_Year - Prior_Year) / Prior_Year

# Budget utilization
Budget_Utilization = Actuals / Budget

# Cost share by product line
Cost_Share_Pct = Product_Line_Cost / Total_Portfolio_Cost
```

### 4.3 Essential Dashboard Views

Build at minimum these four views:

1. **Executive summary**: Total spend, variance to baseline, YoY change, budget utilization
2. **Product line breakdown**: Cost by product line with drill-down to cost pool
3. **Variance waterfall**: Which cost drivers are responsible for the variance
4. **Trend view**: Monthly cost trajectory for each product line

---

## Step 5: Establish Ongoing Operations

### Monthly Workflow

```
Month-End Close Checklist:
[ ] Pull driver data for the period (MAU, MAD, TPS, Units, Headcount)
[ ] Run pre-attribution validation
[ ] Execute allocation model
[ ] Run post-attribution validation
[ ] Compare to prior period — investigate anomalies > 20%
[ ] Refresh BI dashboard
[ ] Distribute to stakeholders
```

### Quarterly Methodology Review

Every quarter, review:
- Are the driver-to-pool mappings still accurate? (Cost structures change)
- Has any new cost pool been added that needs a driver assignment?
- Are the driver data sources still reliable?
- Has the business changed in a way that affects the consumption patterns?

---

## Troubleshooting

**Problem: Allocations don't sum to total spend**
- Check that every cost dollar is assigned to exactly one cost pool
- Verify the cost pool totals equal your general ledger
- Look for rounding errors in percentage calculations

**Problem: One product line's allocation changed dramatically**
- Verify the driver data for that product line is correct
- Check if the cost pool total changed significantly
- Review whether the driver-to-pool mapping is still appropriate

**Problem: Stakeholders are questioning the new allocations**
- Prepare a clear comparison: old method vs. new method, with explanation of why the change is more accurate
- Show the operational data that drives the new allocation
- Offer to walk through the methodology for any cost pool they want to understand

**Problem: Driver data is missing for a product line**
- Investigate why the data is missing — is the product line genuinely consuming zero of this resource?
- If zero is correct, document it
- If the data is simply unavailable, consider using headcount as a proxy while you work to get the right data

---

## Getting Help

- **Open an issue** on this repository with your implementation question
- **Connect on LinkedIn**: [Emmanuel Cudjoe](https://www.linkedin.com/in/ecudjoe123)
- **Read the methodology**: [methodology.md](methodology.md)
- **Industry-specific guidance**: [industry_applications.md](industry_applications.md)

---

*This getting started guide is part of the AI Cost Attribution Framework. See [README.md](../README.md) for framework overview.*
