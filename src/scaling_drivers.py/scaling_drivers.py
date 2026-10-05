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
