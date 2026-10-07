# Security, Governance, and Compliance

## Overview

This document provides guidance for deploying the AI Cost Attribution Framework in enterprise environments where data security, governance controls, and regulatory compliance are requirements rather than considerations.

The framework is designed from the ground up to support enterprise deployment without proprietary dependencies. All security, governance, and compliance capabilities described here are implementable using open-source tools and standard organizational controls — no vendor licensing required.

---

## 1. Data Security

### 1.1 What Data the Framework Processes

Understanding what data the framework actually handles is the foundation of any security assessment.

**The framework processes:**
- Operational driver metrics — aggregate counts and volumes by product line or business unit (MAU, MAD, TPS, unit volume, headcount, consumption metrics)
- Cost pool totals — aggregate financial amounts by cost category
- Allocation percentages — derived from driver data
- Validation outputs — statistical checks on allocation results

**The framework does NOT process:**
- Patient-level data (healthcare)
- Individual transaction records (financial services)
- Customer personally identifiable information (PII)
- Proprietary pricing or margin data
- Individual employee data

All driver metrics are aggregate operational statistics at the product line or business unit level. This design is intentional — the methodology requires only the summary-level data needed to calculate allocation shares, not the underlying transaction or individual records.

### 1.2 Data Classification

Classify the data flowing through your implementation:

| Data Type | Typical Classification | Recommended Handling |
|---|---|---|
| Driver metric totals (MAU, units, etc.) | Internal | Standard access controls |
| Cost pool amounts | Confidential | Finance team access only |
| Allocation percentages | Confidential | Finance team access only |
| Final allocated P&L by product line | Restricted | Senior leadership + finance |
| Validation logs | Internal | Finance operations team |
| Methodology documentation | Internal | Available to all implementers |

### 1.3 Data Residency and Processing

**Principle: Data stays inside your environment**

The framework is deployed entirely within your organization's infrastructure. No data is transmitted to external services, APIs, or third-party platforms. The open-source tools the framework uses (Python, Apache Superset, standard BI tools) process data locally.

**Implementation requirements:**
- Deploy all framework components within your organization's network perimeter
- Use your organization's existing data storage infrastructure (on-premise or cloud tenant)
- If using cloud infrastructure, ensure data residency requirements are met for your jurisdiction and industry
- Do not connect driver data sources to external APIs without explicit security review

### 1.4 Encryption Standards

**Data at rest:**
- Encrypt all cost attribution data stores using AES-256 or equivalent
- Apply encryption to both input driver data and output allocation results
- Use your organization's standard key management infrastructure

**Data in transit:**
- Enforce TLS 1.2+ for all data movement between framework components
- Use encrypted connections for all database queries and BI tool data sources
- Do not transmit cost allocation data over unencrypted channels

**Implementation note:** If deploying on AWS, Azure, or GCP, use native encryption services (AWS KMS, Azure Key Vault, GCP Cloud KMS) rather than implementing custom encryption.

---

## 2. Access Control and Identity Management

### 2.1 Role-Based Access Control (RBAC)

Implement least-privilege access across all framework components.

**Recommended role structure:**

| Role | Access Level | Responsibilities |
|---|---|---|
| Methodology Owner | Full read/write | Designs and updates driver mappings; approves methodology changes |
| Finance Analyst | Read allocation outputs; write driver inputs | Collects and submits driver data; reviews allocation results |
| Finance Manager | Read all outputs; approve driver data | Reviews and approves driver data before attribution runs |
| Business Partner | Read own product line allocations only | Views cost allocations for their product line; cannot see other lines |
| Auditor | Read all outputs and logs; no write | Reviews methodology, logs, and historical allocations |
| System Administrator | Infrastructure access only | Manages deployment; cannot see financial data |

**Implementation:**
```python
# Example: Role-based data filtering for self-service analytics
def get_allocation_data(user_role: str, product_line: str = None):
    """
    Return allocation data filtered by user role.
    Business partners see only their own product line.
    Finance and above see all product lines.
    """
    finance_roles = ['methodology_owner', 'finance_analyst',
                     'finance_manager', 'auditor']

    if user_role in finance_roles:
        return fetch_all_allocations()
    elif user_role == 'business_partner' and product_line:
        return fetch_allocation_for_product(product_line)
    else:
        raise PermissionError(f"Role '{user_role}' does not have access to allocation data")
```

### 2.2 Authentication

- Integrate with your organization's existing identity provider (Active Directory, Okta, Azure AD)
- Enforce multi-factor authentication for all users with access to cost allocation data
- Use service accounts with limited permissions for automated attribution runs
- Rotate service account credentials quarterly

### 2.3 API Security (if applicable)

If your implementation exposes attribution results through an internal API:

```python
# Example: API authentication middleware
from functools import wraps

def require_auth(required_role: str):
    """Decorator to enforce role-based access on API endpoints."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = get_auth_token_from_request()
            user = validate_token(token)
            if not user or user.role not in get_permitted_roles(required_role):
                raise PermissionError("Insufficient permissions")
            return func(*args, **kwargs)
        return wrapper
    return decorator

@require_auth('finance_analyst')
def get_allocation_results(period: str):
    """Protected endpoint for allocation results."""
    pass
```

---

## 3. Governance Framework

### 3.1 Methodology Change Control

Every change to the attribution methodology — driver assignments, cost pool boundaries, allocation formulas — must follow a documented change control process. Undocumented methodology changes create audit risk and undermine stakeholder trust in the allocation results.

**Change control process:**

```
1. PROPOSAL: Finance analyst or methodology owner proposes change
   → Document: what is changing, why, expected impact on allocations

2. REVIEW: Finance manager reviews proposal
   → Assess: magnitude of P&L impact, stakeholder communication needs

3. IMPACT ANALYSIS: Run parallel attribution with old and new methodology
   → Document: before/after comparison by product line

4. APPROVAL: Methodology owner and finance leadership approve
   → Sign-off required before implementation

5. COMMUNICATION: Notify affected stakeholders
   → Share before/after comparison; explain rationale for change

6. IMPLEMENTATION: Apply change with effective date documentation
   → Update version history; preserve prior period methodology

7. AUDIT TRAIL: Log change in methodology change register
   → Who proposed, who approved, effective date, change description
```

### 3.2 Methodology Versioning

Maintain a version history of your attribution methodology. Preserve prior period methodologies — you will need them for historical comparison and audit response.

**Version register structure:**

```markdown
## Methodology Version Register

| Version | Effective Date | Changed By | Approved By | Summary of Changes |
|---|---|---|---|---|
| v1.0 | 2026-01-01 | [Name] | [Name] | Initial methodology — 5 drivers, 14 fleet types |
| v1.1 | 2026-04-01 | [Name] | [Name] | Added Device Cloud Services to MAU driver |
| v1.2 | 2026-07-01 | [Name] | [Name] | Revised Headcount driver scope |
```

### 3.3 Driver Data Governance

**Data owner assignment**

Each driver metric must have a named data owner — the person or team responsible for providing accurate, timely driver data each period.

| Driver | Data Owner | Source System | Submission Deadline |
|---|---|---|---|
| MAU | Product Analytics team | Analytics platform | 3rd business day |
| MAD | Device Engineering | Device telemetry system | 3rd business day |
| TPS | Platform Engineering | Monitoring system | 3rd business day |
| Unit Volume | Supply Chain Finance | ERP system | 2nd business day |
| Headcount | HR/People Analytics | HRIS | 1st business day |
| Consumption Metrics | Infrastructure Engineering | Cloud billing API | 2nd business day |

**Driver data validation before attribution**

Require data owners to certify driver data accuracy before each attribution run:

```python
def require_data_owner_certification(driver_data: dict, certifications: dict) -> bool:
    """
    Verify all driver data owners have certified their data
    before running attribution.

    Args:
        driver_data: {driver_name: data}
        certifications: {driver_name: {'certified_by': str, 'certified_at': datetime}}

    Returns:
        True if all drivers are certified, raises ValueError otherwise
    """
    uncertified = [d for d in driver_data if d not in certifications]
    if uncertified:
        raise ValueError(
            f"Attribution cannot proceed. The following driver data has not been "
            f"certified by the data owner: {uncertified}"
        )
    return True
```

### 3.4 Audit Trail

Maintain a complete audit trail of every attribution run.

**Attribution run log — required fields:**

```python
attribution_run_log = {
    'run_id': 'unique identifier',
    'period': '2026-Q3',
    'methodology_version': 'v1.2',
    'run_timestamp': '2026-10-01T09:15:00Z',
    'run_by': 'service_account_attribution',
    'driver_data_versions': {
        'MAU': {'submitted_by': 'analytics_team', 'submitted_at': '2026-10-01T08:00:00Z'},
        'Units': {'submitted_by': 'supply_chain_finance', 'submitted_at': '2026-10-01T07:30:00Z'},
    },
    'validation_results': {
        'completeness_check': 'PASS',
        'sum_check': 'PASS',
        'prior_period_variance': 'PASS'
    },
    'output_hash': 'sha256 hash of allocation output file',
    'approved_by': 'finance_manager_name',
    'approved_at': '2026-10-01T10:00:00Z'
}
```

Store attribution run logs for a minimum of seven years — consistent with standard financial record retention requirements.

---

## 4. Regulatory Compliance

### 4.1 SOX Compliance (Financial Services, Public Companies)

The Sarbanes-Oxley Act requires that internal controls over financial reporting (ICFR) are documented, tested, and effective. Cost attribution methodology is part of ICFR when it affects product-level P&L reporting.

**SOX requirements for cost attribution:**

**Documentation (SOX Section 302/404):**
- Document the cost attribution methodology completely, including driver selection rationale
- Maintain version history with effective dates
- Document all manual adjustments with approval evidence

**Access controls:**
- Segregate duties — the person who submits driver data should not be the same person who runs attribution
- Restrict write access to attribution models to the methodology owner
- Log all access to attribution systems

**Change management:**
- All methodology changes require documented approval before implementation
- Changes affecting material product line P&L require senior finance sign-off
- Test methodology changes in a non-production environment before deploying

**Testing:**
- Test attribution controls at least annually (quarterly recommended)
- Document test results and remediation of any control failures
- Maintain evidence of testing for external auditor review

### 4.2 HIPAA Compliance (Healthcare)

The Health Insurance Portability and Accountability Act governs the protection of Protected Health Information (PHI). Cost attribution implementations in healthcare must ensure PHI is not used as attribution input data.

**HIPAA compliance requirements:**

**Use aggregate data only:**
- Driver metrics must be department-level aggregates, never patient-level data
- Patient encounter counts, procedure volumes, and bed-days are operational statistics — they are not PHI when reported at the department level without individual patient identifiers

**Business Associate Agreement (BAA):**
- If your cost attribution implementation uses cloud services that may process PHI, execute a BAA with the cloud provider before deployment
- Review whether your BI tool vendor requires a BAA in your environment

**Minimum necessary standard:**
- Collect only the driver data necessary for attribution — do not pull patient records or clinical data into the attribution system

**Implementation checklist:**
```
Healthcare HIPAA Compliance Checklist:
[ ] All driver data is aggregate (department level), not patient level
[ ] No patient identifiers (name, DOB, MRN) in any attribution dataset
[ ] BAA executed with any cloud vendor processing data in healthcare environment
[ ] Access logs maintained for all cost data access
[ ] Attribution system included in annual HIPAA risk assessment
[ ] Staff with attribution system access completed HIPAA training
```

### 4.3 FDA 21 CFR Part 11 (Pharmaceutical Manufacturing)

For pharmaceutical manufacturers operating under FDA oversight, electronic records and audit trails must comply with 21 CFR Part 11 requirements when cost systems are part of regulated operations.

**Applicable when:** Your cost attribution system is connected to or feeds into GMP-regulated manufacturing cost systems.

**21 CFR Part 11 requirements:**

**Electronic signatures:**
- Data owner certifications and methodology approvals must be electronically signed by authorized individuals
- Electronic signatures must be unique to one individual and linked to their identity

**Audit trail:**
- The attribution system must generate time-stamped audit trails for all record creation, modification, and deletion
- Audit trails must be computer-generated and tamper-evident
- Users must not be able to modify their own audit trail entries

**System validation:**
- If the attribution system is part of a regulated process, it requires formal validation (IQ/OQ/PQ)
- Maintain validation documentation and evidence

**Note:** If cost attribution feeds only management accounting (not GMP-regulated operations), 21 CFR Part 11 may not apply. Consult your regulatory affairs team.

### 4.4 GDPR and International Data Privacy (Global Organizations)

For organizations operating in the European Union or processing data of EU residents:

**Data minimization:**
- Collect only the driver data necessary for attribution
- Do not retain driver data beyond the period required for attribution and audit purposes

**Data residency:**
- If EU employee headcount data is used as a driver, ensure it remains within the EU or in a jurisdiction with an adequacy decision
- Use data processing agreements with any vendors processing EU data

**Retention periods:**
- Align attribution data retention to your organization's data retention schedule
- Implement automated deletion of driver data after the retention period expires

---

## 5. Open-Source Deployment Security

### 5.1 Dependency Management

The framework uses minimal external dependencies by design. Before deploying, audit all dependencies:

```bash
# Audit Python dependencies for known vulnerabilities
pip install safety
safety check

# Keep dependencies updated
pip list --outdated
pip install --upgrade [package]
```

**Recommended dependency review cadence:** Monthly for production deployments.

### 5.2 Code Review Before Deployment

Before deploying this framework in a production environment:

1. **Review `scaling_drivers.py`**: Understand every function before deploying. The code is intentionally simple and readable — no black boxes.
2. **Review any customizations**: If you extend the framework with industry-specific functions, have the code reviewed by a second developer before production deployment.
3. **Test with synthetic data**: Run the full attribution workflow with synthetic data before connecting to production systems.

### 5.3 Secrets Management

If your implementation connects to databases, cloud APIs, or BI tools that require credentials:

```python
# DO NOT hardcode credentials
# BAD:
db_password = "my_actual_password"

# GOOD: Use environment variables
import os
db_password = os.environ.get('ATTRIBUTION_DB_PASSWORD')

# BETTER: Use a secrets manager
import boto3  # or Azure Key Vault, GCP Secret Manager, HashiCorp Vault
secrets_client = boto3.client('secretsmanager')
secret = secrets_client.get_secret_value(SecretId='attribution-db-credentials')
```

---

## 6. Governance Checklist for New Deployments

Before going live with a new cost attribution implementation, complete this governance checklist:

```
Pre-Deployment Governance Checklist:

SECURITY
[ ] Data classification completed for all attribution data
[ ] Encryption at rest implemented for all data stores
[ ] Encryption in transit enforced for all data movement
[ ] No PII or patient-level data in attribution datasets
[ ] Secrets management implemented (no hardcoded credentials)

ACCESS CONTROL
[ ] RBAC roles defined and implemented
[ ] Authentication integrated with organizational identity provider
[ ] MFA enforced for all users with access to cost data
[ ] Segregation of duties verified (data submission ≠ attribution run)
[ ] Service account permissions scoped to minimum necessary

GOVERNANCE
[ ] Methodology documentation complete and approved
[ ] Driver data owners assigned for each metric
[ ] Change control process documented and communicated
[ ] Version register initialized
[ ] Attribution run log structure implemented

COMPLIANCE (apply as relevant to your industry)
[ ] SOX: ICFR documentation complete
[ ] HIPAA: Aggregate-only data confirmed; BAA executed if required
[ ] FDA: 21 CFR Part 11 applicability assessed; validation completed if required
[ ] GDPR: Data residency and retention requirements addressed

AUDIT READINESS
[ ] Attribution run logs retained per retention policy
[ ] Methodology version history preserved
[ ] Change approvals documented with evidence
[ ] Access logs enabled and retained
```

---

## Contributing

If you are implementing this framework in a regulated industry and have developed additional compliance guidance — particularly for industries not covered here (energy, government, education, defense) — contributions are welcome.

Open an issue or submit a pull request with your industry-specific compliance guidance.

---

*This security, governance, and compliance guide is part of the AI Cost Attribution Framework. See [README.md](../README.md) for framework overview and [methodology.md](methodology.md) for methodology documentation.*
