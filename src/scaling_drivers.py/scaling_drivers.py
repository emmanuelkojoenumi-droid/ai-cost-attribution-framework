"""
scaling_drivers.py
==================
Utility functions for calculating and validating the five operational
scaling drivers used in the AI Cost Attribution Framework.

The five drivers:
    1. Active User Metrics (MAU / MAD)
    2. Transaction Throughput (TPS)
    3. Unit Volume
    4. Headcount
    5. Consumption Metrics

Each driver function:
    - Accepts a dictionary of {product_line: value} pairs
    - Returns a dictionary of {product_line: share_percentage} pairs
    - Validates that shares sum to 100%

Author: Emmanuel Cudjoe
Framework: AI Cost Attribution Framework
License: MIT
"""

from typing import Dict, Optional
import warnings


# ---------------------------------------------------------------------------
# Core Driver Calculation Functions
# ---------------------------------------------------------------------------

def calculate_driver_shares(driver_data: Dict[str, float]) -> Dict[str, float]:
    """
    Convert raw driver values to percentage shares.

    The fundamental calculation underlying all five drivers:
    each product line's share equals its driver value divided
    by the total, expressed as a percentage.

    Args:
        driver_data: {product_line: raw_driver_value}
                     e.g. {'SMP': 71.0, 'Partner_TV': 17.7, 'Amazon_TV': 2.0}

    Returns:
        {product_line: share_percentage}
        e.g. {'SMP': 78.89, 'Partner_TV': 19.67, 'Amazon_TV': 2.22}

    Raises:
        ValueError: If all driver values are zero (cannot calculate shares)
        ValueError: If any driver value is negative
    """
    if not driver_data:
        raise ValueError("driver_data cannot be empty")

    if any(v < 0 for v in driver_data.values()):
        negative = {k: v for k, v in driver_data.items() if v < 0}
        raise ValueError(f"Driver values cannot be negative: {negative}")

    total = sum(driver_data.values())

    if total == 0:
        raise ValueError(
            "Total driver value is zero — cannot calculate shares. "
            "Verify that at least one product line has a non-zero driver value."
        )

    shares = {
        product_line: (value / total) * 100
        for product_line, value in driver_data.items()
    }

    # Validate shares sum to 100 (within floating point tolerance)
    total_share = sum(shares.values())
    if abs(total_share - 100.0) > 0.01:
        warnings.warn(
            f"Share percentages sum to {total_share:.4f}%, not 100%. "
            "Check for floating point precision issues."
        )

    return shares


def calculate_mau_shares(mau_data: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate cost allocation shares based on Monthly Active Users (MAU).

    Use for: User-facing infrastructure costs that scale with engaged
    user population — content delivery, authentication, user-facing APIs,
    recommendation systems, and similar services.

    Args:
        mau_data: {product_line: monthly_active_users_millions}
                  e.g. {'SMP': 71.0, 'Partner_TV': 17.7, 'Amazon_TV': 2.0}

    Returns:
        {product_line: share_percentage}

    Example:
        >>> mau = {'SMP': 71.0, 'Partner_TV': 17.7, 'Amazon_TV': 2.0}
        >>> shares = calculate_mau_shares(mau)
        >>> print(shares)
        {'SMP': 78.89, 'Partner_TV': 19.67, 'Amazon_TV': 2.22}
    """
    return calculate_driver_shares(mau_data)


def calculate_mad_shares(mad_data: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate cost allocation shares based on Monthly Active Devices (MAD).

    Use for: Device-facing infrastructure costs that scale with active
    device population — device management services, firmware delivery,
    device telemetry processing, and similar services.

    Args:
        mad_data: {product_line: monthly_active_devices_millions}

    Returns:
        {product_line: share_percentage}
    """
    return calculate_driver_shares(mad_data)


def calculate_tps_shares(tps_data: Dict[str, float]) -> Dict[str, float]:
    """
    Calculate cost allocation shares based on Transaction Per Second (TPS).

    Use for: High-availability infrastructure provisioned for PEAK load
    rather than average load. Real-time processing systems, payment
    networks, API gateways, and similar services.

    Important: Use PEAK TPS, not average TPS. Infrastructure must be
    provisioned for the highest demand scenario. A product line that
    generates 30% of peak TPS is responsible for 30% of the provisioning
    cost, even if its average TPS is much lower.

    Args:
        tps_data: {product_line: peak_transactions_per_second}

    Returns:
        {product_line: share_percentage}

    Example:
        >>> tps = {'Payments': 5000, 'Banking': 2000, 'Wealth': 500}
        >>> shares = calculate_tps_shares(tps)
        >>> print(shares)
        {'Payments': 66.67, 'Banking': 26.67, 'Wealth': 6.67}
    """
    return calculate_driver_shares(tps_data)


def calculate_unit_shares(
    unit_data: Dict[str, float],
    unit_type: str = "units"
) -> Dict[str, float]:
    """
    Calculate cost allocation shares based on unit volume.

    Use for: Supply chain, logistics, and physical operations infrastructure
    that scales with physical unit throughput — device management, supply
    chain handling, retail operations, and similar services.

    Args:
        unit_data: {product_line: unit_volume}
                   e.g. {'SMP': 25.3, 'Partner_TV': 12.4, 'Amazon_TV': 0.7}
        unit_type: Description of the unit for documentation
                   e.g. "units", "online_units", "shipments", "batches"

    Returns:
        {product_line: share_percentage}

    Example:
        >>> units = {'SMP': 25.3, 'Partner_TV': 12.4, 'Amazon_TV': 0.7}
        >>> shares = calculate_unit_shares(units, unit_type='online_units')
        >>> print(shares)
        {'SMP': 65.89, 'Partner_TV': 32.29, 'Amazon_TV': 1.82}
    """
    return calculate_driver_shares(unit_data)


def calculate_headcount_shares(
    headcount_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate cost allocation shares based on headcount.

    Use for: Development tools, testing environments, engineering
    infrastructure, and shared support services where no consumption
    metric is available.

    NOTE: Headcount is a proxy driver — it does not measure actual
    consumption of infrastructure. Use headcount ONLY when no consumption-
    based metric is available, and document the rationale clearly.
    Prioritize consumption-based drivers wherever possible.

    Args:
        headcount_data: {product_line: headcount}
                        e.g. {'SMP': 120, 'Partner_TV': 45, 'Amazon_TV': 15}

    Returns:
        {product_line: share_percentage}
    """
    warnings.warn(
        "Headcount is a proxy driver. Consider whether a consumption-based "
        "metric (MAU, TPS, units, or direct consumption) better reflects "
        "actual resource usage for this cost pool.",
        UserWarning,
        stacklevel=2
    )
    return calculate_driver_shares(headcount_data)


def calculate_consumption_shares(
    consumption_data: Dict[str, float],
    unit_of_measure: str = "units"
) -> Dict[str, float]:
    """
    Calculate cost allocation shares based on direct consumption metrics.

    Use for: Cloud infrastructure with available usage telemetry —
    compute hours, storage volume, API calls, data transfer, or
    any directly metered resource.

    This is the most accurate driver when data is available. Prioritize
    consumption metrics over all other drivers.

    Args:
        consumption_data: {product_line: consumption_value}
                          e.g. {'SMP': 450000, 'Partner_TV': 85000, 'Amazon_TV': 12000}
        unit_of_measure: Description of the consumption unit for documentation
                         e.g. "compute_hours", "GB_stored", "API_calls", "GB_transferred"

    Returns:
        {product_line: share_percentage}

    Example:
        >>> consumption = {'SMP': 450000, 'Partner_TV': 85000, 'Amazon_TV': 12000}
        >>> shares = calculate_consumption_shares(consumption, 'compute_hours')
        >>> print(shares)
        {'SMP': 82.57, 'Partner_TV': 15.60, 'Amazon_TV': 2.20}
    """
    return calculate_driver_shares(consumption_data)


# ---------------------------------------------------------------------------
# Driver Validation Functions
# ---------------------------------------------------------------------------

def validate_driver_data(
    driver_data: Dict[str, Dict[str, float]],
    expected_product_lines: Optional[list] = None
) -> Dict[str, dict]:
    """
    Validate a set of driver data before running attribution.

    Checks for:
    - Missing product lines (if expected_product_lines is provided)
    - Zero values (which may indicate missing data rather than zero consumption)
    - Negative values (always an error)
    - Extreme outliers (values > 10x the median — flag for review)

    Args:
        driver_data: {driver_name: {product_line: value}}
                     e.g. {
                         'MAU': {'SMP': 71.0, 'Partner_TV': 17.7},
                         'Units': {'SMP': 25.3, 'Partner_TV': 12.4}
                     }
        expected_product_lines: List of product lines that should appear
                                 in every driver. If None, validation uses
                                 the product lines found in the data.

    Returns:
        Validation results dictionary with structure:
        {
            driver_name: {
                'status': 'PASS' | 'WARNING' | 'FAIL',
                'issues': [list of issue descriptions],
                'total': total driver value,
                'product_line_count': number of product lines
            }
        }

    Example:
        >>> drivers = {
        ...     'MAU': {'SMP': 71.0, 'Partner_TV': 17.7, 'Amazon_TV': 2.0},
        ...     'Units': {'SMP': 25.3, 'Partner_TV': 12.4, 'Amazon_TV': 0.0}
        ... }
        >>> results = validate_driver_data(drivers)
        >>> print(results['Units']['status'])
        'WARNING'
        >>> print(results['Units']['issues'])
        ['Amazon_TV has zero value for Units — verify this is correct']
    """
    if expected_product_lines is None:
        # Infer expected product lines from the union of all drivers
        all_product_lines = set()
        for driver_values in driver_data.values():
            all_product_lines.update(driver_values.keys())
        expected_product_lines = list(all_product_lines)

    validation_results = {}

    for driver_name, values in driver_data.items():
        issues = []
        status = 'PASS'

        # Check for missing product lines
        for pl in expected_product_lines:
            if pl not in values:
                issues.append(
                    f"{pl} is missing from {driver_name} data — "
                    f"will default to zero allocation"
                )
                status = 'WARNING'

        # Check for negative values
        for pl, value in values.items():
            if value < 0:
                issues.append(
                    f"{pl} has negative value ({value}) for {driver_name} — "
                    f"driver values cannot be negative"
                )
                status = 'FAIL'

        # Check for zero values (may be legitimate or may indicate missing data)
        zero_values = [pl for pl, v in values.items() if v == 0]
        for pl in zero_values:
            issues.append(
                f"{pl} has zero value for {driver_name} — "
                f"verify this is correct (zero allocation) rather than missing data"
            )
            if status == 'PASS':
                status = 'WARNING'

        # Check for extreme outliers (> 10x the median)
        if len(values) > 2:
            sorted_values = sorted(v for v in values.values() if v > 0)
            if sorted_values:
                median = sorted_values[len(sorted_values) // 2]
                if median > 0:
                    for pl, value in values.items():
                        if value > median * 10:
                            issues.append(
                                f"{pl} value ({value}) is more than 10x the median "
                                f"({median:.1f}) for {driver_name} — verify this is correct"
                            )
                            if status == 'PASS':
                                status = 'WARNING'

        total = sum(values.values())

        validation_results[driver_name] = {
            'status': status,
            'issues': issues,
            'total': total,
            'product_line_count': len(values),
            'zero_count': len(zero_values)
        }

    return validation_results


def validate_allocation_completeness(
    allocated_costs: Dict[str, float],
    total_cost_pool: float,
    tolerance: float = 0.01
) -> Dict[str, object]:
    """
    Validate that allocated costs sum to the total cost pool.

    This is the most fundamental validation check — allocated costs
    must equal total costs (no dollar should be lost or duplicated).

    Args:
        allocated_costs: {product_line: allocated_cost}
        total_cost_pool: The known total cost that should be fully allocated
        tolerance: Acceptable rounding tolerance (default: $0.01)

    Returns:
        {
            'status': 'PASS' | 'FAIL',
            'allocated_total': sum of allocated costs,
            'expected_total': total_cost_pool,
            'variance': allocated_total - expected_total,
            'variance_pct': variance as percentage of total
        }
    """
    allocated_total = sum(allocated_costs.values())
    variance = allocated_total - total_cost_pool
    variance_pct = (variance / total_cost_pool * 100) if total_cost_pool != 0 else 0

    return {
        'status': 'PASS' if abs(variance) <= tolerance else 'FAIL',
        'allocated_total': allocated_total,
        'expected_total': total_cost_pool,
        'variance': variance,
        'variance_pct': variance_pct
    }


def compare_to_prior_period(
    current_shares: Dict[str, float],
    prior_shares: Dict[str, float],
    variance_threshold: float = 20.0
) -> Dict[str, dict]:
    """
    Compare current period allocation shares to prior period.

    Large period-over-period changes in allocation share may indicate:
    - Genuine shifts in operational activity (expected)
    - Data errors in current or prior period driver data
    - Methodology changes not reflected in the prior period

    Flag changes exceeding the variance threshold for manual review.

    Args:
        current_shares: {product_line: share_percentage} for current period
        prior_shares: {product_line: share_percentage} for prior period
        variance_threshold: Percentage point change that triggers a flag
                            (default: 20 percentage points)

    Returns:
        {product_line: {
            'current_share': float,
            'prior_share': float,
            'change_pp': float,  # change in percentage points
            'flag': bool         # True if change exceeds threshold
        }}
    """
    all_product_lines = set(current_shares.keys()) | set(prior_shares.keys())
    comparison = {}

    for pl in all_product_lines:
        current = current_shares.get(pl, 0.0)
        prior = prior_shares.get(pl, 0.0)
        change = current - prior

        comparison[pl] = {
            'current_share': current,
            'prior_share': prior,
            'change_pp': change,
            'flag': abs(change) >= variance_threshold
        }

    return comparison


# ---------------------------------------------------------------------------
# Convenience Functions
# ---------------------------------------------------------------------------

def calculate_all_driver_shares(driver_dataset: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
    """
    Calculate shares for all drivers in a dataset simultaneously.

    Args:
        driver_dataset: {driver_name: {product_line: value}}

    Returns:
        {driver_name: {product_line: share_percentage}}

    Example:
        >>> dataset = {
        ...     'MAU': {'SMP': 71.0, 'Partner_TV': 17.7, 'Amazon_TV': 2.0},
        ...     'Units': {'SMP': 25.3, 'Partner_TV': 12.4, 'Amazon_TV': 0.7},
        ...     'TPS': {'SMP': 0.0, 'Partner_TV': 0.0, 'Amazon_TV': 0.0}
        ... }
        >>> all_shares = calculate_all_driver_shares(dataset)
    """
    all_shares = {}
    for driver_name, values in driver_dataset.items():
        try:
            all_shares[driver_name] = calculate_driver_shares(values)
        except ValueError as e:
            all_shares[driver_name] = {'error': str(e)}

    return all_shares


def summarize_allocation(
    allocated_costs: Dict[str, float],
    driver_shares: Dict[str, float]
) -> None:
    """
    Print a human-readable summary of allocation results.

    Args:
        allocated_costs: {product_line: allocated_cost}
        driver_shares: {product_line: share_percentage}
    """
    total = sum(allocated_costs.values())
    print(f"\n{'='*55}")
    print(f"{'ALLOCATION SUMMARY':^55}")
    print(f"{'='*55}")
    print(f"{'Product Line':<25} {'Share %':>10} {'Allocated Cost':>15}")
    print(f"{'-'*55}")

    for pl in sorted(allocated_costs.keys()):
        share = driver_shares.get(pl, 0.0)
        cost = allocated_costs[pl]
        print(f"{pl:<25} {share:>9.2f}% {cost:>14,.2f}")

    print(f"{'-'*55}")
    print(f"{'TOTAL':<25} {'100.00%':>10} {total:>14,.2f}")
    print(f"{'='*55}\n")


# ---------------------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Example: Calculating cost allocation shares for a multi-product
    technology portfolio using the five operational scaling drivers.
    """

    print("AI Cost Attribution Framework — Scaling Drivers Example")
    print("=" * 60)

    # Sample driver data (values in millions where applicable)
    sample_drivers = {
        'MAU': {
            'SMP': 71.0,
            'Partner_Branded_TV': 17.7,
            'Amazon_Branded_TV': 2.0,
            'Appstore': 1.5,
            'Accessories': 0.3
        },
        'MAD': {
            'SMP': 100.6,
            'Partner_Branded_TV': 20.1,
            'Amazon_Branded_TV': 2.3,
            'Appstore': 0.0,
            'Accessories': 0.0
        },
        'Units': {
            'SMP': 25.3,
            'Partner_Branded_TV': 12.4,
            'Amazon_Branded_TV': 0.7,
            'Appstore': 0.0,
            'Accessories': 0.3
        },
        'Headcount': {
            'SMP': 120,
            'Partner_Branded_TV': 35,
            'Amazon_Branded_TV': 15,
            'Appstore': 20,
            'Accessories': 10
        }
    }

    # Step 1: Validate driver data
    print("\nStep 1: Validating driver data...")
    validation = validate_driver_data(
        sample_drivers,
        expected_product_lines=['SMP', 'Partner_Branded_TV', 'Amazon_Branded_TV',
                                 'Appstore', 'Accessories']
    )

    for driver, result in validation.items():
        status = result['status']
        symbol = '✓' if status == 'PASS' else ('!' if status == 'WARNING' else '✗')
        print(f"  {symbol} {driver}: {status}")
        for issue in result['issues']:
            print(f"      → {issue}")

    # Step 2: Calculate shares
    print("\nStep 2: Calculating allocation shares...")
    all_shares = calculate_all_driver_shares(sample_drivers)

    for driver, shares in all_shares.items():
        if 'error' not in shares:
            print(f"\n  {driver} Shares:")
            for pl, share in sorted(shares.items(), key=lambda x: x[1], reverse=True):
                print(f"    {pl:<30} {share:>7.2f}%")

    # Step 3: Apply to a cost pool
    print("\nStep 3: Applying MAU shares to user-facing infrastructure cost pool...")
    cost_pool_total = 10_000_000  # $10M user-facing infrastructure

    mau_shares = all_shares['MAU']
    allocated_costs = {
        pl: (share / 100) * cost_pool_total
        for pl, share in mau_shares.items()
    }

    summarize_allocation(allocated_costs, mau_shares)

    # Step 4: Validate completeness
    print("Step 4: Validating allocation completeness...")
    completeness = validate_allocation_completeness(allocated_costs, cost_pool_total)
    status_symbol = '✓' if completeness['status'] == 'PASS' else '✗'
    print(f"  {status_symbol} Completeness check: {completeness['status']}")
    print(f"     Allocated: ${completeness['allocated_total']:,.2f}")
    print(f"     Expected:  ${completeness['expected_total']:,.2f}")
    print(f"     Variance:  ${completeness['variance']:,.2f}")


# ---------------------------------------------------------------------------
# Industry-Specific Driver Functions
# ---------------------------------------------------------------------------
# The five core drivers above apply universally across industries.
# The functions below are industry-specific wrappers that make the
# methodology immediately accessible to practitioners in each sector —
# using the terminology and metrics familiar to their industry context.
# ---------------------------------------------------------------------------


# ── PHARMACEUTICAL MANUFACTURING ────────────────────────────────────────────

def calculate_batch_volume_shares(batch_data: Dict[str, float]) -> Dict[str, float]:
    """
    Pharmaceutical Manufacturing: Allocate shared production facility costs
    by batch volume produced per drug product line.

    Equivalent to: Unit Volume driver in the core framework.

    Use for: Production equipment depreciation, facility utilities,
    quality control infrastructure, and manufacturing overhead costs
    that scale with production activity.

    Args:
        batch_data: {drug_product_line: batches_produced}
                    e.g. {'Drug_A': 450, 'Drug_B': 120, 'Drug_C': 80}

    Returns:
        {drug_product_line: share_percentage}

    Example:
        >>> batches = {'Oncology_Drug_A': 450, 'Cardio_Drug_B': 120, 'Rare_Disease_C': 30}
        >>> shares = calculate_batch_volume_shares(batches)
        >>> print(shares)
        {'Oncology_Drug_A': 75.0, 'Cardio_Drug_B': 20.0, 'Rare_Disease_C': 5.0}

    Real-world context:
        U.S. pharmaceutical manufacturers frequently distribute shared
        production facility costs using headcount or revenue percentage —
        neither of which reflects actual equipment and facility consumption.
        Batch volume is the primary operational driver of production costs:
        each batch consumes equipment time, utilities, QC testing, and
        regulatory compliance activity regardless of the drug's revenue.
    """
    return calculate_driver_shares(batch_data)


def calculate_equipment_utilization_shares(
    utilization_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Pharmaceutical Manufacturing: Allocate shared equipment and maintenance
    costs by actual equipment utilization hours per product line.

    Equivalent to: Consumption Metrics driver in the core framework.

    Use for: Equipment depreciation, preventive maintenance, engineering
    support, and calibration costs that scale with equipment runtime.

    Args:
        utilization_data: {drug_product_line: equipment_hours_used}
                          e.g. {'Drug_A': 1200, 'Drug_B': 450, 'Drug_C': 150}

    Returns:
        {drug_product_line: share_percentage}

    Example:
        >>> hours = {'Oncology_Line': 1200, 'Cardio_Line': 450, 'Rare_Disease_Line': 150}
        >>> shares = calculate_equipment_utilization_shares(hours)
        >>> print(shares)
        {'Oncology_Line': 66.67, 'Cardio_Line': 25.0, 'Rare_Disease_Line': 8.33}
    """
    return calculate_driver_shares(utilization_data)


def calculate_material_consumption_shares(
    material_data: Dict[str, float],
    unit: str = "kg"
) -> Dict[str, float]:
    """
    Pharmaceutical Manufacturing: Allocate raw material handling and
    supply chain infrastructure costs by material consumption volume.

    Equivalent to: Consumption Metrics driver in the core framework.

    Use for: Raw material procurement infrastructure, cold chain costs,
    materials handling, and supply chain overhead.

    Args:
        material_data: {drug_product_line: material_consumed}
                       e.g. {'Drug_A': 5000, 'Drug_B': 1200, 'Drug_C': 300}
        unit: Unit of measure for documentation (e.g. 'kg', 'liters', 'units')

    Returns:
        {drug_product_line: share_percentage}
    """
    return calculate_driver_shares(material_data)


# ── HEALTHCARE SYSTEMS ───────────────────────────────────────────────────────

def calculate_patient_encounter_shares(
    encounter_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Healthcare Systems: Allocate shared administrative and clinical
    infrastructure costs by patient encounter volume per department.

    Equivalent to: Active User Metrics driver in the core framework.

    Use for: EHR and administrative systems, patient registration
    infrastructure, scheduling systems, and general clinical overhead
    that scales with patient volume.

    Args:
        encounter_data: {clinical_department: patient_encounters}
                        e.g. {'Emergency': 8500, 'Surgery': 2100, 'Oncology': 1800}

    Returns:
        {clinical_department: share_percentage}

    Example:
        >>> encounters = {
        ...     'Emergency_Dept': 8500,
        ...     'Surgical_Services': 2100,
        ...     'Oncology': 1800,
        ...     'Cardiology': 3200,
        ...     'Primary_Care': 12000
        ... }
        >>> shares = calculate_patient_encounter_shares(encounters)

    Real-world context:
        Hospital systems typically distribute overhead using bed count or
        patient census — neither reflects how administrative and support
        infrastructure is actually consumed. Patient encounter volume is
        the primary driver of administrative systems, scheduling, and
        support service consumption.
    """
    return calculate_driver_shares(encounter_data)


def calculate_procedure_volume_shares(
    procedure_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Healthcare Systems: Allocate shared clinical equipment and specialty
    infrastructure costs by procedure volume per department.

    Equivalent to: Transaction Throughput driver in the core framework.

    Use for: Imaging equipment (MRI, CT, X-ray), surgical suite
    infrastructure, laboratory systems, and specialty equipment
    costs that scale with procedure volume.

    Args:
        procedure_data: {clinical_department: procedures_performed}
                        e.g. {'Radiology': 4200, 'Surgery': 1800, 'Lab': 22000}

    Returns:
        {clinical_department: share_percentage}

    Example:
        >>> procedures = {
        ...     'Radiology': 4200,
        ...     'Surgical_Services': 1800,
        ...     'Laboratory': 22000,
        ...     'Cardiology': 950,
        ...     'Gastroenterology': 680
        ... }
        >>> shares = calculate_procedure_volume_shares(procedures)
    """
    return calculate_driver_shares(procedure_data)


def calculate_acuity_weighted_bed_days(
    bed_days: Dict[str, float],
    case_mix_index: Dict[str, float]
) -> Dict[str, float]:
    """
    Healthcare Systems: Calculate acuity-weighted bed-days for allocating
    high-dependency and ICU infrastructure costs.

    This is an enhanced version of the Unit Volume driver that adjusts
    raw bed-day counts for patient complexity — recognizing that a high-
    acuity patient consumes significantly more resources per day than a
    low-acuity patient.

    Use for: ICU infrastructure, high-dependency care costs, specialist
    nursing costs, and intensive monitoring systems.

    Args:
        bed_days: {clinical_department: total_bed_days}
        case_mix_index: {clinical_department: CMI_score}
                        CMI > 1.0 = higher than average complexity
                        CMI < 1.0 = lower than average complexity

    Returns:
        {clinical_department: share_percentage}
        (based on acuity-weighted bed-days, not raw bed-days)

    Example:
        >>> bed_days = {'ICU': 1200, 'Med_Surg': 4500, 'Oncology': 800}
        >>> cmi = {'ICU': 4.2, 'Med_Surg': 1.1, 'Oncology': 2.8}
        >>> shares = calculate_acuity_weighted_bed_days(bed_days, cmi)
        >>> # ICU: 1200 × 4.2 = 5040 weighted bed-days
        >>> # Med_Surg: 4500 × 1.1 = 4950 weighted bed-days
        >>> # Oncology: 800 × 2.8 = 2240 weighted bed-days
    """
    weighted = {
        dept: bed_days[dept] * case_mix_index.get(dept, 1.0)
        for dept in bed_days
    }
    return calculate_driver_shares(weighted)


def calculate_or_utilization_shares(
    or_hours: Dict[str, float]
) -> Dict[str, float]:
    """
    Healthcare Systems: Allocate surgical suite infrastructure costs
    by actual OR hours utilized per surgical specialty.

    Equivalent to: Consumption Metrics driver in the core framework.

    Use for: Surgical suite depreciation, surgical equipment maintenance,
    anesthesia infrastructure, surgical nursing overhead, and sterilization
    costs that scale with actual OR time utilized.

    Args:
        or_hours: {surgical_specialty: or_hours_utilized}
                  e.g. {'General_Surgery': 820, 'Orthopedics': 640, 'Cardio': 380}

    Returns:
        {surgical_specialty: share_percentage}
    """
    return calculate_driver_shares(or_hours)


# ── LOGISTICS AND SUPPLY CHAIN ───────────────────────────────────────────────

def calculate_route_miles_shares(
    miles_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Logistics and Supply Chain: Allocate fleet operating costs by
    route miles driven per service tier or customer segment.

    Equivalent to: Consumption Metrics driver in the core framework.

    Use for: Fuel costs, vehicle maintenance, tire and wear costs,
    and driver mileage compensation — all of which scale directly
    with distance driven.

    Args:
        miles_data: {service_tier: route_miles_driven}
                    e.g. {'Same_Day': 45000, 'Standard': 180000, 'Freight': 95000}

    Returns:
        {service_tier: share_percentage}

    Example:
        >>> miles = {
        ...     'Same_Day_Delivery': 45000,
        ...     'Standard_Delivery': 180000,
        ...     'Freight': 95000,
        ...     'Returns': 22000
        ... }
        >>> shares = calculate_route_miles_shares(miles)

    Real-world context:
        Logistics organizations frequently allocate fleet costs using
        revenue percentage or flat rates across service tiers — neither
        reflects actual vehicle consumption. Route miles is the primary
        driver of fuel, maintenance, and depreciation costs.
    """
    return calculate_driver_shares(miles_data)


def calculate_shipment_volume_shares(
    shipment_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Logistics and Supply Chain: Allocate warehouse handling and
    technology infrastructure costs by shipment volume.

    Equivalent to: Transaction Throughput driver in the core framework.

    Use for: Warehouse handling labor, sorting infrastructure, tracking
    technology, and last-mile delivery systems that scale with shipment count.

    Args:
        shipment_data: {service_tier: shipment_count}
                       e.g. {'Same_Day': 12000, 'Standard': 85000, 'Freight': 4200}

    Returns:
        {service_tier: share_percentage}
    """
    return calculate_driver_shares(shipment_data)


def calculate_cwt_miles_shares(
    weight_data: Dict[str, float],
    miles_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Logistics and Supply Chain: Allocate freight infrastructure costs
    using the industry-standard cwt-miles (hundredweight × miles) metric.

    cwt-miles is the standard cost unit in freight logistics — it
    captures both the weight and distance dimensions of freight cost,
    which neither weight alone nor miles alone reflects accurately.

    Equivalent to: Combined Unit Volume × Consumption Metrics drivers.

    Use for: Freight vehicle operating costs, loading dock infrastructure,
    weight-based handling equipment, and long-haul transportation overhead.

    Args:
        weight_data: {service_tier: weight_in_hundredweight_cwt}
        miles_data: {service_tier: route_miles}

    Returns:
        {service_tier: share_percentage}
        (based on weight × miles for each service tier)

    Example:
        >>> weight = {'LTL': 8500, 'FTL': 42000, 'Parcel': 1200}
        >>> miles = {'LTL': 320, 'FTL': 850, 'Parcel': 45}
        >>> shares = calculate_cwt_miles_shares(weight, miles)
        >>> # LTL: 8500 × 320 = 2,720,000 cwt-miles
        >>> # FTL: 42000 × 850 = 35,700,000 cwt-miles
        >>> # Parcel: 1200 × 45 = 54,000 cwt-miles
    """
    cwt_miles = {
        tier: weight_data.get(tier, 0) * miles_data.get(tier, 0)
        for tier in set(weight_data) | set(miles_data)
    }
    return calculate_driver_shares(cwt_miles)


# ── FINANCIAL SERVICES ───────────────────────────────────────────────────────

def calculate_transaction_volume_shares(
    transaction_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Financial Services: Allocate payment processing and core banking
    infrastructure costs by transaction volume per product line.

    Equivalent to: Transaction Throughput driver in the core framework.

    Use for: Payment processing infrastructure, fraud detection systems,
    settlement systems, real-time risk calculation, and core banking
    transaction processing costs.

    Args:
        transaction_data: {product_line: transaction_count}
                          e.g. {'Payments': 45000000, 'Retail_Banking': 12000000}

    Returns:
        {product_line: share_percentage}

    Example:
        >>> transactions = {
        ...     'Payments_Processing': 45_000_000,
        ...     'Retail_Banking': 12_000_000,
        ...     'Commercial_Banking': 3_500_000,
        ...     'Wealth_Management': 280_000,
        ...     'Insurance': 920_000
        ... }
        >>> shares = calculate_transaction_volume_shares(transactions)

    Real-world context:
        Financial services firms frequently attribute technology
        infrastructure costs by revenue percentage — which systematically
        overallocates costs to high-margin, low-volume products (wealth
        management) and underallocates to high-volume, low-margin products
        (payments, retail banking). Transaction volume reflects actual
        system consumption.
    """
    return calculate_driver_shares(transaction_data)


def calculate_active_account_shares(
    account_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Financial Services: Allocate customer-facing technology and data
    infrastructure costs by active account volume per product line.

    Equivalent to: Active User Metrics driver in the core framework.

    Use for: Core banking systems, customer data storage, CRM
    infrastructure, digital banking platforms, and customer service
    systems that scale with active account population.

    Args:
        account_data: {product_line: active_account_count}
                      e.g. {'Checking': 2400000, 'Savings': 1800000, 'Mortgage': 340000}

    Returns:
        {product_line: share_percentage}
    """
    return calculate_driver_shares(account_data)


def calculate_ai_inference_shares(
    inference_data: Dict[str, float]
) -> Dict[str, float]:
    """
    Financial Services / Technology: Allocate AI model infrastructure
    costs by inference API call volume per product line.

    Equivalent to: Consumption Metrics driver in the core framework.

    Use for: GPU compute costs, model hosting infrastructure, inference
    API costs, and AI platform overhead — the fastest-growing and
    most difficult-to-attribute cost category in AI-powered organizations.

    Args:
        inference_data: {product_line: api_calls_or_tokens}
                        e.g. {'Credit_Scoring': 8500000, 'Fraud_Detection': 45000000}

    Returns:
        {product_line: share_percentage}

    Example:
        >>> inference = {
        ...     'Credit_Underwriting': 8_500_000,
        ...     'Fraud_Detection': 45_000_000,
        ...     'Customer_Service_AI': 12_000_000,
        ...     'Risk_Calculation': 6_200_000,
        ...     'Document_Processing': 3_800_000
        ... }
        >>> shares = calculate_ai_inference_shares(inference)

    Real-world context:
        As AI infrastructure investment accelerates across financial
        services, attributing GPU and model inference costs by revenue
        percentage produces increasingly distorted results. High-frequency,
        low-margin AI applications (fraud detection, transaction scoring)
        consume the majority of inference infrastructure but generate
        modest direct revenue. Usage-based attribution using API call
        volume or token consumption directly reflects actual AI cost
        consumption.
    """
    return calculate_driver_shares(inference_data)


def calculate_data_storage_shares(
    storage_data: Dict[str, float],
    unit: str = "GB"
) -> Dict[str, float]:
    """
    Financial Services / Technology: Allocate data storage and management
    infrastructure costs by data volume per product line.

    Equivalent to: Consumption Metrics driver in the core framework.

    Use for: Data warehouse costs, data lake infrastructure, backup and
    archival costs, and data management overhead that scales with
    data volume.

    Args:
        storage_data: {product_line: data_volume}
                      e.g. {'Trading': 45000, 'Banking': 120000, 'Compliance': 380000}
        unit: Unit of measure for documentation (e.g. 'GB', 'TB', 'PB')

    Returns:
        {product_line: share_percentage}
    """
    return calculate_driver_shares(storage_data)


# ---------------------------------------------------------------------------
# Industry Driver Reference Table
# ---------------------------------------------------------------------------

INDUSTRY_DRIVER_REFERENCE = {
    "Technology / Cloud": {
        "Active User Metrics": "Monthly Active Users (MAU), Monthly Active Devices (MAD)",
        "Transaction Throughput": "API requests per second, peak TPS",
        "Unit Volume": "Devices shipped, managed devices",
        "Headcount": "Engineering staff per product line",
        "Consumption Metrics": "Compute hours, GB stored, GB transferred, API calls"
    },
    "Pharmaceutical Manufacturing": {
        "Active User Metrics": "Patients on active treatment programs",
        "Transaction Throughput": "Batch production runs per period",
        "Unit Volume": "Drug units produced, active SKU count",
        "Headcount": "Production line staff",
        "Consumption Metrics": "Equipment utilization hours, raw material kg consumed"
    },
    "Healthcare Systems": {
        "Active User Metrics": "Patient encounters per department",
        "Transaction Throughput": "Procedures performed (imaging, surgical, lab)",
        "Unit Volume": "Patient bed-days (acuity-weighted)",
        "Headcount": "Clinical staff per department",
        "Consumption Metrics": "OR hours utilized, imaging scan count"
    },
    "Logistics and Supply Chain": {
        "Active User Metrics": "Active customer accounts, active shipper accounts",
        "Transaction Throughput": "Shipments processed per period",
        "Unit Volume": "Package count, freight weight (cwt)",
        "Headcount": "Drivers and warehouse staff per service tier",
        "Consumption Metrics": "Route miles driven, fuel consumed, cwt-miles"
    },
    "Financial Services": {
        "Active User Metrics": "Monthly active account holders, digital banking users",
        "Transaction Throughput": "Transactions processed, payment volume",
        "Unit Volume": "Active accounts, policies in force, loans outstanding",
        "Headcount": "Staff per business line",
        "Consumption Metrics": "AI inference calls, data storage GB, compute hours"
    }
}


def print_industry_driver_reference(industry: str = None) -> None:
    """
    Print the driver reference table for one or all industries.

    Args:
        industry: Industry name (optional). If None, prints all industries.
                  Options: 'Technology / Cloud', 'Pharmaceutical Manufacturing',
                           'Healthcare Systems', 'Logistics and Supply Chain',
                           'Financial Services'

    Example:
        >>> print_industry_driver_reference('Healthcare Systems')
        >>> print_industry_driver_reference()  # prints all
    """
    industries = (
        {industry: INDUSTRY_DRIVER_REFERENCE[industry]}
        if industry and industry in INDUSTRY_DRIVER_REFERENCE
        else INDUSTRY_DRIVER_REFERENCE
    )

    for ind_name, drivers in industries.items():
        print(f"\n{'='*60}")
        print(f"  {ind_name}")
        print(f"{'='*60}")
        for driver, equivalent in drivers.items():
            print(f"  {driver:<28} {equivalent}")
    print()
