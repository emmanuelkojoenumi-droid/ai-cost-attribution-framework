"""
data_ingestion.py
=================
Data ingestion and normalization layer for the AI Cost Attribution Framework.

Transforms structured, semi-structured, and partially unstructured data
sources into the clean dictionary format required by the framework's
driver calculation functions.

Supported input formats:
    Structured:
        - Python dictionaries (pass-through)
        - CSV files
        - Pandas DataFrames
        - Excel workbooks (.xlsx, .xls)
        - JSON files

    Semi-Structured:
        - AWS Cost Explorer API responses
        - Azure Cost Management API responses
        - GCP Billing API responses
        - SAP export formats
        - Generic ERP CSV/XML exports
        - Cloud billing CSVs (multi-column, multi-service)

    Partially Unstructured:
        - Operational reports with embedded tables
        - Maintenance logs with key-value patterns
        - Structured text with labeled metrics

Design principle:
    All ingestion functions return the same output format:
        {entity_name: numeric_value}
    This makes every input source compatible with any driver
    calculation function in scaling_drivers.py.

Author: Emmanuel Cudjoe
Framework: AI Cost Attribution Framework
License: MIT
"""

import csv
import json
import re
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# Type alias for the standard framework input format
# ---------------------------------------------------------------------------
DriverData = Dict[str, float]


# ---------------------------------------------------------------------------
# Structured Data Ingestion
# ---------------------------------------------------------------------------

def from_dict(data: dict, value_key: Optional[str] = None) -> DriverData:
    """
    Pass-through normalization for dictionary inputs.

    Handles two common dictionary shapes:
    - Flat: {entity: numeric_value}
    - Nested: {entity: {metric_key: value, ...}}

    Args:
        data: Input dictionary
        value_key: For nested dicts, the key whose value to extract.
                   e.g. value_key='total' extracts data[entity]['total']
                   If None, expects flat {entity: numeric_value} structure.

    Returns:
        {entity: float}

    Example — flat:
        >>> from_dict({'Product_A': 71.0, 'Product_B': 17.7})
        {'Product_A': 71.0, 'Product_B': 17.7}

    Example — nested:
        >>> nested = {
        ...     'Product_A': {'mau': 71.0, 'mad': 100.6},
        ...     'Product_B': {'mau': 17.7, 'mad': 20.1}
        ... }
        >>> from_dict(nested, value_key='mau')
        {'Product_A': 71.0, 'Product_B': 17.7}
    """
    if not data:
        return {}

    if value_key is None:
        # Flat dictionary — validate and convert values to float
        result = {}
        for entity, value in data.items():
            try:
                result[str(entity)] = float(value)
            except (TypeError, ValueError):
                warnings.warn(
                    f"Cannot convert value for '{entity}' to float: {value!r}. "
                    f"Skipping this entry.",
                    UserWarning
                )
        return result
    else:
        # Nested dictionary — extract specified key from each entity
        result = {}
        for entity, metrics in data.items():
            if not isinstance(metrics, dict):
                warnings.warn(
                    f"Expected nested dict for '{entity}', got {type(metrics).__name__}. "
                    f"Skipping.",
                    UserWarning
                )
                continue
            if value_key not in metrics:
                warnings.warn(
                    f"Key '{value_key}' not found for entity '{entity}'. "
                    f"Available keys: {list(metrics.keys())}. Skipping.",
                    UserWarning
                )
                continue
            try:
                result[str(entity)] = float(metrics[value_key])
            except (TypeError, ValueError) as e:
                warnings.warn(f"Cannot convert '{entity}.{value_key}' to float: {e}")
        return result


def from_csv(
    filepath: str,
    entity_col: str,
    value_col: str,
    encoding: str = 'utf-8',
    skip_rows: int = 0,
    filter_col: Optional[str] = None,
    filter_value: Optional[str] = None,
    aggregation: str = 'sum'
) -> DriverData:
    """
    Load driver data from a CSV file.

    Args:
        filepath: Path to the CSV file
        entity_col: Column name containing entity names (product lines,
                    departments, etc.)
        value_col: Column name containing the driver metric values
        encoding: File encoding (default: utf-8)
        skip_rows: Number of header rows to skip before the column headers
        filter_col: Optional column to filter on before extracting data
        filter_value: Value to match in filter_col (exact match)
        aggregation: How to handle multiple rows per entity:
                     'sum' (default), 'mean', 'max', 'min', 'last'

    Returns:
        {entity: float}

    Example:
        >>> # CSV with columns: product_line, month, mau_millions
        >>> data = from_csv(
        ...     'data/driver_data.csv',
        ...     entity_col='product_line',
        ...     value_col='mau_millions',
        ...     filter_col='month',
        ...     filter_value='2026-09'
        ... )

    Handles common CSV quality issues:
        - Extra whitespace in column names and values
        - Comma-formatted numbers (1,234.56)
        - Empty/null values (treated as 0.0 with a warning)
        - Duplicate entity rows (aggregated per aggregation parameter)
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV file not found: {filepath}")

    raw_data: Dict[str, List[float]] = {}

    with open(filepath, encoding=encoding, newline='') as f:
        # Skip header rows if needed
        for _ in range(skip_rows):
            next(f)

        reader = csv.DictReader(f)

        # Normalize column names (strip whitespace)
        if reader.fieldnames:
            reader.fieldnames = [col.strip() for col in reader.fieldnames]

        # Validate required columns
        required_cols = {entity_col, value_col}
        if filter_col:
            required_cols.add(filter_col)

        missing = required_cols - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"Required columns not found in CSV: {missing}. "
                f"Available columns: {reader.fieldnames}"
            )

        for row_num, row in enumerate(reader, start=2):
            # Apply filter if specified
            if filter_col and filter_value:
                if row.get(filter_col, '').strip() != str(filter_value):
                    continue

            entity = row.get(entity_col, '').strip()
            if not entity:
                continue

            raw_value = row.get(value_col, '').strip()

            # Handle empty values
            if not raw_value:
                warnings.warn(
                    f"Row {row_num}: Empty value for entity '{entity}'. "
                    f"Treating as 0.0.",
                    UserWarning
                )
                value = 0.0
            else:
                # Remove common formatting characters
                cleaned = raw_value.replace(',', '').replace('$', '').replace('%', '').strip()
                try:
                    value = float(cleaned)
                except ValueError:
                    warnings.warn(
                        f"Row {row_num}: Cannot parse value '{raw_value}' "
                        f"for entity '{entity}'. Skipping.",
                        UserWarning
                    )
                    continue

            if entity not in raw_data:
                raw_data[entity] = []
            raw_data[entity].append(value)

    # Aggregate multiple rows per entity
    result = {}
    for entity, values in raw_data.items():
        if aggregation == 'sum':
            result[entity] = sum(values)
        elif aggregation == 'mean':
            result[entity] = sum(values) / len(values)
        elif aggregation == 'max':
            result[entity] = max(values)
        elif aggregation == 'min':
            result[entity] = min(values)
        elif aggregation == 'last':
            result[entity] = values[-1]
        else:
            raise ValueError(f"Unknown aggregation method: '{aggregation}'. "
                             f"Use 'sum', 'mean', 'max', 'min', or 'last'.")

    return result


def from_dataframe(
    df,
    entity_col: str,
    value_col: str,
    filter_col: Optional[str] = None,
    filter_value=None,
    aggregation: str = 'sum'
) -> DriverData:
    """
    Load driver data from a Pandas DataFrame.

    Args:
        df: Pandas DataFrame
        entity_col: Column containing entity names
        value_col: Column containing driver metric values
        filter_col: Optional column to filter on
        filter_value: Value to match in filter_col
        aggregation: 'sum', 'mean', 'max', 'min', or 'last'

    Returns:
        {entity: float}

    Example:
        >>> import pandas as pd
        >>> df = pd.read_sql("SELECT product_line, mau FROM driver_metrics WHERE period='2026-09'", conn)
        >>> data = from_dataframe(df, entity_col='product_line', value_col='mau')

    Example with filtering:
        >>> df = pd.read_csv('all_periods.csv')
        >>> data = from_dataframe(
        ...     df,
        ...     entity_col='department',
        ...     value_col='patient_encounters',
        ...     filter_col='period',
        ...     filter_value='2026-Q3'
        ... )
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "Pandas is required for from_dataframe(). "
            "Install it with: pip install pandas"
        )

    # Apply filter
    if filter_col is not None and filter_value is not None:
        df = df[df[filter_col] == filter_value]

    # Validate columns
    for col in [entity_col, value_col]:
        if col not in df.columns:
            raise ValueError(
                f"Column '{col}' not found in DataFrame. "
                f"Available columns: {list(df.columns)}"
            )

    # Aggregate
    agg_map = {'sum': 'sum', 'mean': 'mean', 'max': 'max', 'min': 'min', 'last': 'last'}
    if aggregation not in agg_map:
        raise ValueError(f"Unknown aggregation: '{aggregation}'")

    grouped = df.groupby(entity_col)[value_col].agg(agg_map[aggregation])

    return {str(entity): float(value) for entity, value in grouped.items()
            if not __import__('math').isnan(float(value))}


def from_json(
    filepath: str,
    entity_path: str,
    value_path: str,
    encoding: str = 'utf-8'
) -> DriverData:
    """
    Load driver data from a JSON file.

    Supports two JSON structures:
    1. Object format: {"Product_A": 71.0, "Product_B": 17.7}
    2. Array format: [{"name": "Product_A", "mau": 71.0}, ...]

    For array format, use dot notation paths:
        entity_path = 'name'   (field containing entity name)
        value_path = 'mau'     (field containing the metric value)

    For object format, pass entity_path='' and value_path='':
        The top-level keys become entities, values become driver values.

    For nested JSON, use dot notation:
        entity_path = 'product.name'
        value_path = 'metrics.monthly_active_users'

    Args:
        filepath: Path to JSON file
        entity_path: Dot-notation path to entity name field
        value_path: Dot-notation path to metric value field
        encoding: File encoding

    Returns:
        {entity: float}

    Example — object format:
        >>> # JSON: {"Emergency": 8500, "Surgery": 2100, "Oncology": 1800}
        >>> data = from_json('healthcare_encounters.json', '', '')

    Example — array format:
        >>> # JSON: [{"dept": "Emergency", "visits": 8500}, ...]
        >>> data = from_json('encounters.json', 'dept', 'visits')

    Example — nested:
        >>> # JSON: [{"dept": {"name": "Emergency"}, "metrics": {"visits": 8500}}, ...]
        >>> data = from_json('nested.json', 'dept.name', 'metrics.visits')
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"JSON file not found: {filepath}")

    with open(filepath, encoding=encoding) as f:
        raw = json.load(f)

    def get_nested(obj: dict, path: str):
        """Extract value using dot-notation path."""
        if not path:
            return obj
        parts = path.split('.')
        for part in parts:
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                return None
        return obj

    result = {}

    if isinstance(raw, dict) and not entity_path and not value_path:
        # Object format: top-level keys are entities
        for entity, value in raw.items():
            try:
                result[str(entity)] = float(value)
            except (TypeError, ValueError):
                warnings.warn(f"Cannot convert value for '{entity}': {value!r}")

    elif isinstance(raw, list):
        # Array format: each element is one entity
        for i, item in enumerate(raw):
            entity = get_nested(item, entity_path)
            value = get_nested(item, value_path)

            if entity is None:
                warnings.warn(f"Item {i}: entity path '{entity_path}' not found. Skipping.")
                continue
            if value is None:
                warnings.warn(f"Item {i}: value path '{value_path}' not found. Skipping.")
                continue

            try:
                result[str(entity)] = float(value)
            except (TypeError, ValueError):
                warnings.warn(f"Item {i}: Cannot convert '{value}' to float for '{entity}'.")

    else:
        raise ValueError(
            "JSON structure not recognized. Expected either:\n"
            "  - Object: {entity_name: value, ...}\n"
            "  - Array: [{entity_field: name, value_field: value}, ...]"
        )

    return result


def from_excel(
    filepath: str,
    entity_col: str,
    value_col: str,
    sheet_name: Union[str, int] = 0,
    header_row: int = 0,
    filter_col: Optional[str] = None,
    filter_value=None,
    aggregation: str = 'sum'
) -> DriverData:
    """
    Load driver data from an Excel workbook (.xlsx or .xls).

    Args:
        filepath: Path to Excel file
        entity_col: Column name or letter containing entity names
        value_col: Column name or letter containing driver values
        sheet_name: Sheet name (string) or index (int, 0-based)
        header_row: Row index of the column headers (0-based)
        filter_col: Optional column to filter on
        filter_value: Value to match in filter_col
        aggregation: 'sum', 'mean', 'max', 'min', or 'last'

    Returns:
        {entity: float}

    Example:
        >>> data = from_excel(
        ...     'driver_data.xlsx',
        ...     entity_col='Product Line',
        ...     value_col='MAU (millions)',
        ...     sheet_name='Q3 2026',
        ...     filter_col='Month',
        ...     filter_value='September'
        ... )
    """
    try:
        import pandas as pd
    except ImportError:
        raise ImportError(
            "Pandas is required for from_excel(). "
            "Install it with: pip install pandas openpyxl"
        )

    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Excel file not found: {filepath}")

    df = pd.read_excel(filepath, sheet_name=sheet_name, header=header_row)

    return from_dataframe(
        df,
        entity_col=entity_col,
        value_col=value_col,
        filter_col=filter_col,
        filter_value=filter_value,
        aggregation=aggregation
    )


# ---------------------------------------------------------------------------
# Semi-Structured Data Ingestion — Cloud Billing APIs
# ---------------------------------------------------------------------------

def from_aws_cost_explorer(
    response: dict,
    group_by_dimension: str = 'SERVICE',
    metric: str = 'UnblendedCost'
) -> DriverData:
    """
    Parse AWS Cost Explorer API response into driver data.

    Use for: Attributing AWS infrastructure costs by service,
    account, or tag dimension using actual consumption data.

    Args:
        response: Raw response from boto3 ce.get_cost_and_usage()
        group_by_dimension: Dimension to group by ('SERVICE', 'LINKED_ACCOUNT',
                            'USAGE_TYPE', or a cost allocation tag key)
        metric: Cost metric to extract ('UnblendedCost', 'BlendedCost',
                'AmortizedCost', 'UsageQuantity')

    Returns:
        {service_or_dimension: cost_float}

    Example:
        >>> import boto3
        >>> ce = boto3.client('ce', region_name='us-east-1')
        >>> response = ce.get_cost_and_usage(
        ...     TimePeriod={'Start': '2026-09-01', 'End': '2026-09-30'},
        ...     Granularity='MONTHLY',
        ...     Metrics=['UnblendedCost'],
        ...     GroupBy=[{'Type': 'DIMENSION', 'Key': 'SERVICE'}]
        ... )
        >>> service_costs = from_aws_cost_explorer(response)

    Schema reference:
        response['ResultsByTime'][0]['Groups'] is a list of:
        {
            'Keys': ['Amazon EC2'],
            'Metrics': {'UnblendedCost': {'Amount': '12345.67', 'Unit': 'USD'}}
        }
    """
    result = {}

    results_by_time = response.get('ResultsByTime', [])
    if not results_by_time:
        warnings.warn("AWS Cost Explorer response contains no ResultsByTime data.")
        return result

    # Aggregate across all time periods (sum if multiple months returned)
    for period in results_by_time:
        groups = period.get('Groups', [])

        if not groups:
            # No grouping — total cost only
            total = period.get('Total', {}).get(metric, {})
            amount = total.get('Amount', '0')
            try:
                result['Total'] = result.get('Total', 0) + float(amount)
            except ValueError:
                warnings.warn(f"Cannot parse total amount: {amount!r}")
            continue

        for group in groups:
            keys = group.get('Keys', [])
            entity = ' | '.join(keys) if keys else 'Unknown'

            metrics = group.get('Metrics', {})
            metric_data = metrics.get(metric, {})
            amount = metric_data.get('Amount', '0')

            try:
                result[entity] = result.get(entity, 0) + float(amount)
            except ValueError:
                warnings.warn(f"Cannot parse amount for '{entity}': {amount!r}")

    return result


def from_azure_cost_management(
    response: dict,
    group_by_column: str = 'ServiceName'
) -> DriverData:
    """
    Parse Azure Cost Management API response into driver data.

    Args:
        response: Raw response from Azure Cost Management Query API
        group_by_column: Column name to group costs by
                         ('ServiceName', 'ResourceGroup', 'SubscriptionName',
                          or a tag name)

    Returns:
        {service_or_dimension: cost_float}

    Example:
        >>> from azure.mgmt.costmanagement import CostManagementClient
        >>> # ... authenticate and query ...
        >>> azure_costs = from_azure_cost_management(response, 'ServiceName')

    Schema reference:
        response['properties']['rows'] is a list of row arrays
        response['properties']['columns'] is a list of column definitions
    """
    result = {}

    properties = response.get('properties', response)
    columns = properties.get('columns', [])
    rows = properties.get('rows', [])

    if not columns or not rows:
        warnings.warn("Azure Cost Management response contains no data.")
        return result

    # Build column index
    col_names = [col.get('name', '') for col in columns]

    # Find cost and group columns
    cost_col_idx = None
    group_col_idx = None

    for i, name in enumerate(col_names):
        if name.lower() in ('cost', 'pretaxcost', 'usagequantity', 'costinbillingcurrency'):
            if cost_col_idx is None:
                cost_col_idx = i
        if name.lower() == group_by_column.lower() or name == group_by_column:
            group_col_idx = i

    if cost_col_idx is None:
        raise ValueError(
            f"No cost column found. Available columns: {col_names}"
        )
    if group_col_idx is None:
        raise ValueError(
            f"Group column '{group_by_column}' not found. "
            f"Available columns: {col_names}"
        )

    for row in rows:
        try:
            entity = str(row[group_col_idx]) if row[group_col_idx] else 'Unknown'
            value = float(row[cost_col_idx])
            result[entity] = result.get(entity, 0) + value
        except (IndexError, TypeError, ValueError) as e:
            warnings.warn(f"Cannot parse row {row}: {e}")

    return result


def from_gcp_billing(
    response: dict,
    group_by_field: str = 'service.description'
) -> DriverData:
    """
    Parse GCP Billing API / BigQuery billing export into driver data.

    Args:
        response: Dict representation of GCP billing data
                  (from BigQuery export or Cloud Billing API)
        group_by_field: Field path to group by (dot notation for nested)

    Returns:
        {service_or_dimension: cost_float}

    Example — from BigQuery result:
        >>> # Query: SELECT service.description, SUM(cost) as total_cost
        >>> # FROM billing_export WHERE DATE(usage_start_time) = '2026-09-01'
        >>> # GROUP BY service.description
        >>> gcp_costs = from_gcp_billing(bq_result, 'service.description')
    """
    def get_nested_value(obj, path):
        parts = path.split('.')
        for part in parts:
            if isinstance(obj, dict):
                obj = obj.get(part)
            else:
                return None
        return obj

    result = {}

    rows = response if isinstance(response, list) else response.get('rows', [])

    for row in rows:
        entity = get_nested_value(row, group_by_field)
        cost = (
            get_nested_value(row, 'cost') or
            get_nested_value(row, 'total_cost') or
            get_nested_value(row, 'cost_amount')
        )

        if entity is None or cost is None:
            continue

        try:
            result[str(entity)] = result.get(str(entity), 0) + float(cost)
        except (TypeError, ValueError) as e:
            warnings.warn(f"Cannot parse cost for '{entity}': {e}")

    return result


# ---------------------------------------------------------------------------
# Semi-Structured Data Ingestion — Generic Formats
# ---------------------------------------------------------------------------

def from_cloud_billing_csv(
    filepath: str,
    service_col: str,
    cost_col: str,
    product_line_tag_col: Optional[str] = None,
    period_col: Optional[str] = None,
    period_value: Optional[str] = None
) -> DriverData:
    """
    Parse cloud billing CSV exports (AWS, Azure, or GCP format).

    Cloud billing CSVs typically have one row per service per day,
    with hundreds of service line items that need to be aggregated
    by product line or service category.

    Args:
        filepath: Path to the billing CSV export
        service_col: Column containing the service name
        cost_col: Column containing the cost amount
        product_line_tag_col: Optional column containing a product line tag
                              (e.g., AWS Cost Allocation Tag column)
                              If provided, groups by product line rather than service
        period_col: Optional column containing billing period
        period_value: Optional period filter value (e.g., '2026-09')

    Returns:
        If product_line_tag_col provided: {product_line: total_cost}
        Otherwise: {service_name: total_cost}
    """
    group_col = product_line_tag_col if product_line_tag_col else service_col

    return from_csv(
        filepath=filepath,
        entity_col=group_col,
        value_col=cost_col,
        filter_col=period_col,
        filter_value=period_value,
        aggregation='sum'
    )


def from_key_value_text(
    text: str,
    entity_pattern: str = r'([A-Za-z][A-Za-z0-9_\s\-]+?):\s*([\d,\.]+)',
    value_group: int = 2,
    entity_group: int = 1,
    strip_chars: str = ',$'
) -> DriverData:
    """
    Extract driver data from text containing key-value patterns.

    Handles partially unstructured text — operational reports,
    maintenance logs, or summary documents where metrics appear
    as labeled values.

    Args:
        text: Input text containing labeled metrics
        entity_pattern: Regex pattern with capture groups for entity and value
        entity_group: Capture group index for entity name (1-based)
        value_group: Capture group index for numeric value (1-based)
        strip_chars: Characters to strip from values before parsing

    Returns:
        {entity: float}

    Example — maintenance log:
        >>> log = '''
        ... Production Line A: 1,245 equipment hours
        ... Production Line B: 892 equipment hours
        ... Production Line C: 334 equipment hours
        ... '''
        >>> data = from_key_value_text(log)
        >>> print(data)
        {'Production Line A': 1245.0, 'Production Line B': 892.0, ...}

    Example — operational summary:
        >>> summary = '''
        ... Emergency Department: 8,547 patient encounters
        ... Surgical Services: 2,103 patient encounters
        ... Oncology: 1,847 patient encounters
        ... '''
        >>> data = from_key_value_text(summary)

    Example — custom pattern for specific formats:
        >>> # Format: "Drug A | Batches: 450"
        >>> data = from_key_value_text(
        ...     text,
        ...     entity_pattern=r'(Drug [A-Z]+) [|] Batches: ([0-9]+)',
        ...     entity_group=1,
        ...     value_group=2
        ... )
    """
    result = {}

    matches = re.finditer(entity_pattern, text)
    for match in matches:
        try:
            entity = match.group(entity_group).strip()
            raw_value = match.group(value_group).strip()

            # Clean the value
            for char in strip_chars:
                raw_value = raw_value.replace(char, '')
            raw_value = raw_value.strip()

            value = float(raw_value)
            # Aggregate if entity appears multiple times
            result[entity] = result.get(entity, 0) + value

        except (IndexError, ValueError) as e:
            warnings.warn(f"Cannot parse match '{match.group(0)}': {e}")

    if not result:
        warnings.warn(
            "No matches found. Check that your entity_pattern matches "
            "the text format. Use Python's re.finditer() to test your pattern."
        )

    return result


# ---------------------------------------------------------------------------
# Multi-Source Aggregation
# ---------------------------------------------------------------------------

def merge_driver_sources(
    sources: List[DriverData],
    aggregation: str = 'sum',
    fill_missing: float = 0.0
) -> DriverData:
    """
    Merge multiple driver data sources into a single dataset.

    Use when driver data for the same metric comes from multiple
    sources — for example, MAU data from both a production database
    and a CSV export that need to be combined.

    Args:
        sources: List of driver data dictionaries to merge
        aggregation: How to combine values for the same entity:
                     'sum' — add values (default, for splitting data across files)
                     'mean' — average values (for combining estimates)
                     'max' — take the highest value
                     'min' — take the lowest value
                     'first' — take the first non-zero value found
        fill_missing: Value to use for entities missing from some sources
                      (default: 0.0)

    Returns:
        {entity: float}

    Example — merging regional data files:
        >>> north_region = from_csv('north_mau.csv', 'product', 'mau')
        >>> south_region = from_csv('south_mau.csv', 'product', 'mau')
        >>> total_mau = merge_driver_sources([north_region, south_region], 'sum')

    Example — combining estimates with actual data:
        >>> actuals = from_csv('actuals.csv', 'dept', 'encounters')
        >>> estimates = from_csv('estimates.csv', 'dept', 'encounters')
        >>> best_available = merge_driver_sources([actuals, estimates], 'first')
    """
    if not sources:
        return {}

    # Collect all entities across all sources
    all_entities = set()
    for source in sources:
        all_entities.update(source.keys())

    result = {}
    for entity in all_entities:
        values = []
        for source in sources:
            val = source.get(entity)
            if val is not None:
                values.append(val)
            elif fill_missing is not None:
                values.append(fill_missing)

        if not values:
            continue

        if aggregation == 'sum':
            result[entity] = sum(values)
        elif aggregation == 'mean':
            result[entity] = sum(values) / len(values)
        elif aggregation == 'max':
            result[entity] = max(values)
        elif aggregation == 'min':
            result[entity] = min(values)
        elif aggregation == 'first':
            non_zero = [v for v in values if v != 0]
            result[entity] = non_zero[0] if non_zero else 0.0
        else:
            raise ValueError(f"Unknown aggregation: '{aggregation}'")

    return result


def normalize_entity_names(
    data: DriverData,
    name_map: Optional[Dict[str, str]] = None,
    lowercase: bool = False,
    strip_whitespace: bool = True
) -> DriverData:
    """
    Standardize entity names across driver data sources.

    Critical for merging data from multiple systems where the same
    entity may be named differently:
    - "Emergency Dept" vs "Emergency Department" vs "ED"
    - "Product A" vs "product_a" vs "PRODUCT A"

    Args:
        data: Driver data with potentially inconsistent entity names
        name_map: Optional explicit mapping of raw names to standard names
                  e.g. {'ED': 'Emergency Department', 'Surg': 'Surgery'}
        lowercase: If True, convert all entity names to lowercase
        strip_whitespace: If True, strip leading/trailing whitespace

    Returns:
        Driver data with standardized entity names

    Example:
        >>> raw_data = {
        ...     '  Emergency Dept ': 8500,
        ...     'SURGERY': 2100,
        ...     'onco': 1800
        ... }
        >>> name_map = {'onco': 'Oncology', 'SURGERY': 'Surgery'}
        >>> normalized = normalize_entity_names(raw_data, name_map=name_map)
        >>> print(normalized)
        {'Emergency Dept': 8500, 'Surgery': 2100, 'Oncology': 1800}
    """
    result = {}

    for entity, value in data.items():
        normalized = str(entity)

        if strip_whitespace:
            normalized = normalized.strip()
        if lowercase:
            normalized = normalized.lower()
        if name_map and normalized in name_map:
            normalized = name_map[normalized]
        elif name_map and entity in name_map:
            normalized = name_map[entity]

        # Handle duplicate entity names after normalization
        if normalized in result:
            warnings.warn(
                f"Entity name collision after normalization: '{normalized}'. "
                f"Values will be summed.",
                UserWarning
            )
            result[normalized] += value
        else:
            result[normalized] = value

    return result


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_ingested_data(
    data: DriverData,
    min_entities: int = 2,
    allow_zeros: bool = True,
    allow_negatives: bool = False
) -> Dict[str, object]:
    """
    Validate ingested driver data before passing to attribution functions.

    Args:
        data: Ingested driver data to validate
        min_entities: Minimum number of entities required (default: 2)
        allow_zeros: Whether zero values are acceptable (default: True)
        allow_negatives: Whether negative values are acceptable (default: False)

    Returns:
        {
            'status': 'PASS' | 'WARNING' | 'FAIL',
            'entity_count': int,
            'issues': list of issue descriptions,
            'zero_entities': list of entities with zero values,
            'negative_entities': list of entities with negative values
        }
    """
    issues = []
    status = 'PASS'

    if not data:
        return {
            'status': 'FAIL',
            'entity_count': 0,
            'issues': ['No data — ingestion returned empty result'],
            'zero_entities': [],
            'negative_entities': []
        }

    entity_count = len(data)
    zero_entities = [e for e, v in data.items() if v == 0]
    negative_entities = [e for e, v in data.items() if v < 0]

    if entity_count < min_entities:
        issues.append(
            f"Only {entity_count} entity found — attribution requires at least "
            f"{min_entities} entities. Check ingestion parameters."
        )
        status = 'FAIL'

    if zero_entities and not allow_zeros:
        issues.append(
            f"Zero values found for: {zero_entities}. "
            f"These entities will receive zero allocation."
        )
        status = 'WARNING' if status == 'PASS' else status

    if zero_entities and allow_zeros:
        issues.append(
            f"Note: {len(zero_entities)} entities have zero values "
            f"and will receive zero allocation: {zero_entities}"
        )

    if negative_entities and not allow_negatives:
        issues.append(
            f"Negative values found for: {negative_entities}. "
            f"Driver values cannot be negative."
        )
        status = 'FAIL'

    return {
        'status': status,
        'entity_count': entity_count,
        'issues': issues,
        'zero_entities': zero_entities,
        'negative_entities': negative_entities
    }


# ---------------------------------------------------------------------------
# Convenience: End-to-End Ingestion Pipeline
# ---------------------------------------------------------------------------

def ingest_and_validate(
    source_type: str,
    validate: bool = True,
    **kwargs
) -> DriverData:
    """
    Single-function interface for ingesting and validating driver data
    from any supported source type.

    Args:
        source_type: One of 'dict', 'csv', 'json', 'excel', 'dataframe',
                     'aws', 'azure', 'gcp', 'text'
        validate: Whether to run validation after ingestion (default: True)
        **kwargs: Arguments passed to the specific ingestion function

    Returns:
        Validated driver data dict

    Example:
        >>> data = ingest_and_validate('csv',
        ...     filepath='mau_data.csv',
        ...     entity_col='product_line',
        ...     value_col='mau_millions'
        ... )

        >>> data = ingest_and_validate('aws',
        ...     response=ce_response,
        ...     group_by_dimension='SERVICE'
        ... )

        >>> data = ingest_and_validate('text',
        ...     text=maintenance_log_content
        ... )
    """
    source_map = {
        'dict': from_dict,
        'csv': from_csv,
        'json': from_json,
        'excel': from_excel,
        'dataframe': from_dataframe,
        'aws': from_aws_cost_explorer,
        'azure': from_azure_cost_management,
        'gcp': from_gcp_billing,
        'text': from_key_value_text,
        'cloud_csv': from_cloud_billing_csv,
    }

    if source_type not in source_map:
        raise ValueError(
            f"Unknown source_type: '{source_type}'. "
            f"Supported types: {list(source_map.keys())}"
        )

    data = source_map[source_type](**kwargs)

    if validate:
        validation = validate_ingested_data(data)
        if validation['status'] == 'FAIL':
            raise ValueError(
                f"Ingested data failed validation:\n" +
                '\n'.join(f"  - {issue}" for issue in validation['issues'])
            )
        elif validation['status'] == 'WARNING':
            for issue in validation['issues']:
                warnings.warn(issue, UserWarning)

    return data


# ---------------------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("AI Cost Attribution Framework — Data Ingestion Layer")
    print("=" * 60)

    # Example 1: From dictionary
    print("\nExample 1: From dictionary")
    dict_data = from_dict({'Product_A': 71.0, 'Product_B': 17.7, 'Product_C': 2.0})
    print(f"  Result: {dict_data}")

    # Example 2: From key-value text (partial unstructured)
    print("\nExample 2: From operational report text")
    report_text = """
    Monthly Operations Summary — September 2026

    Patient Encounters by Department:
    Emergency Department: 8,547
    Surgical Services: 2,103
    Oncology: 1,847
    Cardiology: 3,241
    Primary Care: 12,089
    """
    text_data = from_key_value_text(report_text)
    print(f"  Extracted {len(text_data)} departments:")
    for dept, value in sorted(text_data.items(), key=lambda x: x[1], reverse=True):
        print(f"    {dept:<30} {value:,.0f}")

    # Example 3: Validate ingested data
    print("\nExample 3: Validate ingested data")
    validation = validate_ingested_data(dict_data)
    print(f"  Status: {validation['status']}")
    print(f"  Entity count: {validation['entity_count']}")
    if validation['issues']:
        for issue in validation['issues']:
            print(f"  Issue: {issue}")
    else:
        print("  No issues found")

    # Example 4: Normalize entity names
    print("\nExample 4: Normalize entity names")
    inconsistent = {
        '  Emergency Dept  ': 8547,
        'SURGICAL SERVICES': 2103,
        'onco': 1847
    }
    name_map = {
        'SURGICAL SERVICES': 'Surgical Services',
        'onco': 'Oncology'
    }
    normalized = normalize_entity_names(inconsistent, name_map=name_map)
    print(f"  Normalized: {normalized}")

    # Example 5: Use with scaling drivers
    print("\nExample 5: Full pipeline — ingest → validate → calculate shares")
    from scaling_drivers import calculate_driver_shares

    shares = calculate_driver_shares(text_data)
    print(f"  Allocation shares from operational report:")
    for dept, share in sorted(shares.items(), key=lambda x: x[1], reverse=True):
        print(f"    {dept:<30} {share:>7.2f}%")
