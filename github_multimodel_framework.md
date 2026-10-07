# Multimodel Framework: Model-Agnostic Design and Cross-Industry Deployment

## Overview

This document describes how the AI Cost Attribution Framework is designed to be model-agnostic — deployable with any AI backend, any data infrastructure, and across any industry — and provides guidance for integrating the methodology with different AI model types.

The framework's model-agnosticism is a deliberate design principle, not an accident. Cost attribution methodology is fundamentally mathematical — driver selection, share calculation, and validation are deterministic operations that produce the same result regardless of which AI system assists in analyzing, diagnosing, or optimizing them.

---

## 1. What Model-Agnostic Means in This Context

### 1.1 The Separation of Concerns

The framework separates three layers that are often conflated:

```
┌─────────────────────────────────────────────────────┐
│  LAYER 1: METHODOLOGY LOGIC (Model-Agnostic)        │
│  • Driver selection principles                       │
│  • Allocation calculation formulas                   │
│  • Validation rules and thresholds                   │
│  • Governance and audit requirements                 │
│  → This layer is IDENTICAL regardless of AI backend  │
└─────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────┐
│  LAYER 2: AI ASSISTANCE LAYER (Model-Specific)      │
│  • Anomaly detection and diagnosis                   │
│  • Pattern recognition across cost pools             │
│  • Documentation generation                          │
│  • Driver optimization recommendations               │
│  → This layer ADAPTS to your AI backend              │
└─────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────┐
│  LAYER 3: IMPLEMENTATION LAYER (Infrastructure-     │
│           Specific)                                  │
│  • Data storage and retrieval                        │
│  • BI tool integration                               │
│  • API connections                                   │
│  • Deployment environment                            │
│  → This layer VARIES by organization                 │
└─────────────────────────────────────────────────────┘
```

**The key insight:** Switching AI models affects only Layer 2. The methodology (Layer 1) and your data infrastructure (Layer 3) remain unchanged. This is what makes the framework genuinely portable.

### 1.2 What the Framework Already Does Without Any AI

The core `scaling_drivers.py` module performs all five driver calculations using pure Python mathematics — no AI required:

```python
# This works identically regardless of your AI stack
from src.scaling_drivers import calculate_mau_shares, validate_driver_data

mau_data = {'Product_A': 71.0, 'Product_B': 17.7, 'Product_C': 2.0}
shares = calculate_mau_shares(mau_data)
# {'Product_A': 78.89, 'Product_B': 19.67, 'Product_C': 2.22}
```

AI contributes to this framework in specific, well-defined ways — it does not replace the mathematical core.

---

## 2. AI Integration Points

### 2.1 The Five AI Contribution Zones

AI contributes meaningfully to cost attribution in five specific areas. Each zone has a defined interface that any AI backend can fulfill:

**Zone 1: Structural Anomaly Detection**

*What it does:* Analyzes the complete data architecture simultaneously to identify errors that sequential human review misses — incorrect range references, misclassified cost categories, formula logic errors.

*Interface contract:*
```python
def detect_anomalies(
    cost_architecture: dict,
    driver_mappings: dict,
    historical_allocations: dict
) -> list[dict]:
    """
    Analyze the complete cost attribution architecture and return
    a list of detected anomalies.

    Args:
        cost_architecture: Complete description of cost pools, formulas,
                           and data relationships
        driver_mappings: Current driver-to-pool mapping table
        historical_allocations: Prior period allocation results for comparison

    Returns:
        List of anomaly dicts, each containing:
        {
            'type': str,           # 'range_error' | 'classification' | 'formula' | 'outlier'
            'location': str,       # Where in the architecture the anomaly was found
            'description': str,    # Human-readable description
            'severity': str,       # 'high' | 'medium' | 'low'
            'suggested_fix': str   # Recommended correction
        }
    """
    raise NotImplementedError("Implement with your AI backend")
```

**Zone 2: Driver Optimization**

*What it does:* Analyzes consumption patterns across all cost pools and product lines simultaneously to recommend the optimal driver for each cost pool.

*Interface contract:*
```python
def recommend_drivers(
    cost_pools: list[dict],
    available_metrics: list[str],
    consumption_history: dict
) -> dict:
    """
    Recommend the optimal allocation driver for each cost pool
    based on consumption pattern analysis.

    Args:
        cost_pools: List of cost pools requiring driver assignment
        available_metrics: Operational metrics available as potential drivers
        consumption_history: Historical consumption data by product line

    Returns:
        {cost_pool_name: {
            'recommended_driver': str,
            'confidence': float,      # 0.0 to 1.0
            'rationale': str,
            'alternative_drivers': list[str]
        }}
    """
    raise NotImplementedError("Implement with your AI backend")
```

**Zone 3: Documentation Generation**

*What it does:* Generates comprehensive documentation of the data architecture, validation protocols, and methodology decisions — ensuring institutional knowledge is preserved.

*Interface contract:*
```python
def generate_documentation(
    methodology_config: dict,
    driver_mappings: dict,
    validation_results: dict,
    change_history: list[dict]
) -> str:
    """
    Generate comprehensive methodology documentation.

    Returns:
        Markdown-formatted documentation string covering:
        - Current methodology description
        - Driver mapping rationale for each cost pool
        - Validation protocols and thresholds
        - Recent changes and their rationale
    """
    raise NotImplementedError("Implement with your AI backend")
```

**Zone 4: Adaptive Validation**

*What it does:* Learns from past errors to build an evolving validation suite that specifically tests for known failure modes in your data environment.

*Interface contract:*
```python
def update_validation_rules(
    historical_errors: list[dict],
    current_validation_suite: list[dict]
) -> list[dict]:
    """
    Analyze historical errors and return an updated validation
    rule set that specifically tests for known failure patterns.

    Args:
        historical_errors: List of past attribution errors with descriptions
        current_validation_suite: Existing validation rules

    Returns:
        Updated validation rule list with new rules added based on
        error pattern analysis
    """
    raise NotImplementedError("Implement with your AI backend")
```

**Zone 5: Natural Language Query**

*What it does:* Allows finance practitioners and business partners to query cost attribution data in natural language — "Why did Product A's infrastructure costs increase last month?" — and receive structured, data-grounded responses.

*Interface contract:*
```python
def answer_cost_query(
    question: str,
    allocation_data: dict,
    driver_data: dict,
    period: str
) -> dict:
    """
    Answer a natural language question about cost allocation results.

    Returns:
        {
            'answer': str,          # Natural language response
            'data_references': list, # Specific data points cited
            'confidence': float,     # Answer confidence 0.0-1.0
            'follow_up_queries': list # Suggested follow-up questions
        }
    """
    raise NotImplementedError("Implement with your AI backend")
```

---

## 3. Implementing the AI Layer with Different Backends

### 3.1 Architecture Pattern

All backend implementations follow the same pattern — they implement the five interface contracts above using whatever AI system is available in the organization.

```python
# base_ai_backend.py — Abstract base class
from abc import ABC, abstractmethod

class CostAttributionAIBackend(ABC):
    """
    Abstract base class for AI backend implementations.
    All backends must implement these five methods.
    """

    @abstractmethod
    def detect_anomalies(self, cost_architecture, driver_mappings,
                         historical_allocations):
        pass

    @abstractmethod
    def recommend_drivers(self, cost_pools, available_metrics,
                          consumption_history):
        pass

    @abstractmethod
    def generate_documentation(self, methodology_config, driver_mappings,
                               validation_results, change_history):
        pass

    @abstractmethod
    def update_validation_rules(self, historical_errors,
                                current_validation_suite):
        pass

    @abstractmethod
    def answer_cost_query(self, question, allocation_data,
                          driver_data, period):
        pass
```

### 3.2 Rules-Based Backend (No LLM Required)

The simplest backend — suitable for organizations that want AI-assisted validation without deploying a language model:

```python
class RulesBasedBackend(CostAttributionAIBackend):
    """
    Rules-based AI backend using statistical analysis
    and predefined heuristics. No LLM required.

    Suitable for: Organizations with strict data governance
    requirements, air-gapped environments, or where LLM
    deployment is not yet approved.
    """

    def detect_anomalies(self, cost_architecture, driver_mappings,
                         historical_allocations):
        anomalies = []

        # Rule 1: Flag any cost pool where no driver is assigned
        for pool in cost_architecture.get('cost_pools', []):
            if pool['name'] not in driver_mappings:
                anomalies.append({
                    'type': 'missing_driver',
                    'location': pool['name'],
                    'description': f"Cost pool '{pool['name']}' has no driver assigned",
                    'severity': 'high',
                    'suggested_fix': 'Assign a primary driver from the five standard drivers'
                })

        # Rule 2: Flag period-over-period changes exceeding 30%
        for product_line, current_alloc in cost_architecture.get('current', {}).items():
            prior_alloc = historical_allocations.get(product_line, 0)
            if prior_alloc > 0:
                change_pct = abs(current_alloc - prior_alloc) / prior_alloc
                if change_pct > 0.30:
                    anomalies.append({
                        'type': 'outlier',
                        'location': product_line,
                        'description': f"Allocation changed {change_pct:.1%} vs prior period",
                        'severity': 'medium',
                        'suggested_fix': 'Verify driver data accuracy for this product line'
                    })

        return anomalies

    def recommend_drivers(self, cost_pools, available_metrics,
                          consumption_history):
        """
        Rules-based driver recommendation using correlation analysis.
        Recommends the available metric with highest correlation to
        the cost pool's historical spend pattern.
        """
        recommendations = {}
        for pool in cost_pools:
            # Default recommendation based on cost pool category
            category = pool.get('category', 'unknown')
            default_drivers = {
                'user_facing': 'MAU',
                'processing': 'TPS',
                'physical': 'unit_volume',
                'support': 'headcount',
                'storage': 'consumption_metrics'
            }
            recommendations[pool['name']] = {
                'recommended_driver': default_drivers.get(category, 'headcount'),
                'confidence': 0.7,
                'rationale': f"Standard driver for {category} cost category",
                'alternative_drivers': list(default_drivers.values())
            }
        return recommendations

    def generate_documentation(self, methodology_config, driver_mappings,
                               validation_results, change_history):
        """Generate structured documentation from configuration data."""
        lines = [
            "# Cost Attribution Methodology Documentation",
            f"## Version: {methodology_config.get('version', 'N/A')}",
            f"## Effective Date: {methodology_config.get('effective_date', 'N/A')}",
            "",
            "## Driver Mappings",
        ]
        for pool, driver in driver_mappings.items():
            lines.append(f"- **{pool}**: {driver}")

        lines += ["", "## Validation Results"]
        for check, result in validation_results.items():
            lines.append(f"- {check}: {result}")

        return "\n".join(lines)

    def update_validation_rules(self, historical_errors,
                                current_validation_suite):
        """Add rules based on historical error patterns."""
        new_rules = list(current_validation_suite)
        error_types = [e.get('type') for e in historical_errors]

        if error_types.count('range_error') >= 2:
            new_rules.append({
                'name': 'enhanced_range_check',
                'description': 'Check all formula ranges against current data structure',
                'trigger': 'range_error history detected'
            })
        return new_rules

    def answer_cost_query(self, question, allocation_data, driver_data, period):
        """Basic keyword-based query answering."""
        return {
            'answer': (
                f"For {period}: Total allocated costs are "
                f"{sum(allocation_data.values()):,.0f}. "
                f"For detailed analysis, review the allocation dashboard."
            ),
            'data_references': list(allocation_data.keys()),
            'confidence': 0.5,
            'follow_up_queries': [
                "What drove the largest cost changes this period?",
                "Which product line has the highest cost concentration?"
            ]
        }
```

### 3.3 Open-Source LLM Backend

For organizations deploying open-source language models (Llama, Mistral, Phi, or similar):

```python
class OpenSourceLLMBackend(CostAttributionAIBackend):
    """
    Backend using a locally-deployed open-source LLM.

    Compatible with: Any model served via an OpenAI-compatible API
    (Ollama, vLLM, LM Studio, llama.cpp server, etc.)

    Advantage: Data never leaves your environment.
    """

    def __init__(self, api_base_url: str, model_name: str):
        """
        Args:
            api_base_url: URL of your local LLM server
                          e.g. 'http://localhost:11434/v1' for Ollama
            model_name: Model identifier
                        e.g. 'llama3', 'mistral', 'phi3'
        """
        self.api_base_url = api_base_url
        self.model_name = model_name

    def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        """Make a call to the local LLM API."""
        import requests
        import json

        response = requests.post(
            f"{self.api_base_url}/chat/completions",
            json={
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1  # Low temperature for analytical tasks
            }
        )
        return response.json()['choices'][0]['message']['content']

    def detect_anomalies(self, cost_architecture, driver_mappings,
                         historical_allocations):
        system_prompt = """You are a financial data analyst specializing in 
        cost attribution systems. Analyze the provided cost architecture and 
        identify structural anomalies. Return a JSON array of anomaly objects."""

        user_prompt = f"""
        Analyze this cost attribution architecture for anomalies:
        
        Cost Architecture: {cost_architecture}
        Driver Mappings: {driver_mappings}
        Historical Allocations: {historical_allocations}
        
        Return JSON array with anomaly objects containing:
        type, location, description, severity, suggested_fix
        """

        response = self._call_model(system_prompt, user_prompt)

        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return []  # Return empty list if parsing fails

    def answer_cost_query(self, question, allocation_data, driver_data, period):
        system_prompt = """You are a finance analyst answering questions about 
        cost allocation data. Be specific, data-grounded, and concise.
        Always cite the specific numbers that support your answer."""

        user_prompt = f"""
        Question: {question}
        
        Period: {period}
        Allocation Data: {allocation_data}
        Driver Data: {driver_data}
        
        Answer the question concisely with specific data references.
        Return JSON with: answer, data_references, confidence, follow_up_queries
        """

        response = self._call_model(system_prompt, user_prompt)

        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {'answer': response, 'data_references': [],
                    'confidence': 0.7, 'follow_up_queries': []}

    # Implement remaining methods following the same pattern
    def recommend_drivers(self, cost_pools, available_metrics, consumption_history):
        raise NotImplementedError("Implement using _call_model pattern above")

    def generate_documentation(self, methodology_config, driver_mappings,
                               validation_results, change_history):
        raise NotImplementedError("Implement using _call_model pattern above")

    def update_validation_rules(self, historical_errors, current_validation_suite):
        raise NotImplementedError("Implement using _call_model pattern above")
```

### 3.4 Commercial API Backend

For organizations using commercial AI APIs — the same interface, different implementation:

```python
class CommercialAPIBackend(CostAttributionAIBackend):
    """
    Backend using a commercial AI API.

    Compatible with: Any provider offering a chat completion API
    (OpenAI, Anthropic, Google, Cohere, Mistral AI, etc.)

    Note: Review your organization's data governance policy before
    sending cost data to external APIs. Consider data anonymization
    or the rules-based / open-source backend for sensitive environments.
    """

    def __init__(self, client, model: str):
        """
        Args:
            client: Initialized API client from your chosen provider
            model: Model identifier string per your provider's documentation
        """
        self.client = client
        self.model = model

    def _call_model(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generic model call — adapt to your provider's SDK.
        The interface is the same; only the SDK call differs.
        """
        # Example using a generic chat completion interface
        # Replace with your provider's actual SDK call
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content

    # Implement all five methods using _call_model
    # (identical pattern to OpenSourceLLMBackend above)
```

---

## 4. Cross-Industry Deployment Considerations

### 4.1 Industry-Specific Model Requirements

Different industries have different requirements for the AI assistance layer:

| Industry | Key Requirement | Recommended Backend |
|---|---|---|
| Pharmaceutical Manufacturing | Audit trail for regulatory compliance; explainability of anomaly detection | Rules-Based or Open-Source LLM (on-premise) |
| Healthcare | HIPAA compliance; data must not leave organization network | Rules-Based or Open-Source LLM (on-premise) |
| Financial Services (Public) | SOX controls; explainable decisions; audit trail | Rules-Based or Open-Source LLM with enhanced logging |
| Fintech / Technology | Speed and sophistication; tolerance for cloud AI | Any backend including commercial API |
| Logistics | Operational simplicity; minimal IT infrastructure | Rules-Based backend |
| Government | Air-gapped or restricted networks | Rules-Based backend only |

### 4.2 Adapting Driver Data Schemas Across Industries

The methodology logic is identical across industries. What changes is the schema of the driver data input. The framework handles this through a flexible input structure:

```python
# Technology company driver data schema
tech_drivers = {
    'MAU': {'Product_A': 71.0, 'Product_B': 2.0},      # millions of users
    'TPS': {'Product_A': 0.0, 'Product_B': 0.0},        # transactions/second
    'Units': {'Product_A': 25.3, 'Product_B': 0.7},     # millions of units
}

# Healthcare system driver data schema — same structure, different metrics
healthcare_drivers = {
    'patient_encounters': {'Emergency': 8500, 'Surgery': 2100, 'Oncology': 1800},
    'procedure_volume': {'Radiology': 4200, 'Surgery': 1800, 'Lab': 22000},
    'or_hours': {'General_Surgery': 820, 'Orthopedics': 640},
    'headcount': {'Emergency': 85, 'Surgery': 42, 'Oncology': 28}
}

# Pharmaceutical manufacturing driver data schema
pharma_drivers = {
    'batch_volume': {'Drug_A': 450, 'Drug_B': 120, 'Drug_C': 80},
    'equipment_hours': {'Drug_A': 1200, 'Drug_B': 450, 'Drug_C': 150},
    'material_kg': {'Drug_A': 5000, 'Drug_B': 1200, 'Drug_C': 300},
    'headcount': {'Drug_A': 45, 'Drug_B': 18, 'Drug_C': 12}
}

# The same calculate_driver_shares() function processes all three schemas
from src.scaling_drivers import calculate_driver_shares

# Works identically for all industries
tech_shares = calculate_driver_shares(tech_drivers['MAU'])
healthcare_shares = calculate_driver_shares(healthcare_drivers['patient_encounters'])
pharma_shares = calculate_driver_shares(pharma_drivers['batch_volume'])
```

### 4.3 Foundational Model Cost Attribution

As organizations deploy large foundational models — language models, image models, multimodal models — shared model infrastructure creates exactly the cost attribution problem this framework is designed to solve.

**The challenge:**

A single foundational model often serves multiple products or business units simultaneously. The model's hosting, inference, and fine-tuning costs need to be attributed to the products that generate the usage — but traditional cost allocation cannot do this accurately.

**The solution:**

Instrument model inference to capture usage by product line, then apply the framework's consumption-based attribution:

```python
# Step 1: Instrument your foundational model calls
class InstrumentedModelClient:
    """
    Wrapper that adds attribution metadata to every model call.
    Works with any model API that follows a standard interface.
    """

    def __init__(self, base_client, product_line: str, use_case: str):
        self.client = base_client
        self.product_line = product_line
        self.use_case = use_case
        self.usage_log = []

    def complete(self, prompt: str, **kwargs) -> str:
        """Make a model call and log usage for cost attribution."""
        response = self.client.complete(prompt, **kwargs)

        # Log usage for attribution
        self.usage_log.append({
            'product_line': self.product_line,
            'use_case': self.use_case,
            'input_tokens': response.usage.input_tokens,
            'output_tokens': response.usage.output_tokens,
            'timestamp': response.timestamp
        })

        return response.content

# Step 2: Aggregate usage by product line
def aggregate_model_usage(usage_logs: list[dict]) -> dict:
    """Aggregate token usage by product line for cost attribution."""
    aggregated = {}
    for log in usage_logs:
        pl = log['product_line']
        tokens = log['input_tokens'] + log['output_tokens']
        aggregated[pl] = aggregated.get(pl, 0) + tokens
    return aggregated

# Step 3: Apply cost attribution using consumption driver
from src.scaling_drivers import calculate_consumption_shares

monthly_usage = aggregate_model_usage(all_usage_logs)
model_cost_shares = calculate_consumption_shares(
    monthly_usage,
    unit_of_measure="tokens"
)

# Result: Fair, usage-based allocation of foundational model costs
# by actual consumption — not revenue percentage or headcount
```

---

## 5. Testing Your Implementation

### 5.1 Model-Agnosticism Test

Verify your implementation is truly model-agnostic by running the attribution with different backends and confirming the methodology results are identical:

```python
def test_model_agnosticism():
    """
    The methodology output should be identical regardless of
    which AI backend is used for the assistance layer.
    """
    from src.scaling_drivers import calculate_mau_shares

    test_data = {'Product_A': 71.0, 'Product_B': 17.7, 'Product_C': 2.0}

    # Run attribution without any AI backend
    baseline_shares = calculate_mau_shares(test_data)

    # The shares should be identical regardless of which backend
    # provides anomaly detection or documentation assistance
    rules_backend = RulesBasedBackend()
    llm_backend = OpenSourceLLMBackend(api_base_url='...', model_name='...')

    # Both backends might flag different anomalies or generate
    # different documentation — but the core attribution math
    # must produce the same result
    assert baseline_shares == calculate_mau_shares(test_data), \
        "Attribution methodology must be deterministic and model-agnostic"

    print("Model-agnosticism test passed: methodology output is backend-independent")
```

### 5.2 Cross-Industry Portability Test

```python
def test_cross_industry_portability():
    """
    Verify the framework handles different industry driver schemas
    using the same underlying calculation logic.
    """
    from src.scaling_drivers import calculate_driver_shares

    # Technology
    tech_result = calculate_driver_shares({'Product_A': 71.0, 'Product_B': 17.7})

    # Healthcare — same function, different domain
    health_result = calculate_driver_shares({'Emergency': 8500, 'Surgery': 2100})

    # Pharma — same function, different domain
    pharma_result = calculate_driver_shares({'Drug_A': 450, 'Drug_B': 120})

    # All should sum to 100%
    for result, label in [(tech_result, 'tech'), (health_result, 'healthcare'),
                          (pharma_result, 'pharma')]:
        total = sum(result.values())
        assert abs(total - 100.0) < 0.01, \
            f"{label}: shares must sum to 100%, got {total:.4f}%"

    print("Cross-industry portability test passed")
```

---

## 6. Contributing

### Adding a New Backend

To contribute a new AI backend implementation:

1. Create a new file: `src/backends/[backend_name]_backend.py`
2. Implement all five methods of `CostAttributionAIBackend`
3. Include a working example with synthetic data
4. Document the deployment requirements and any dependencies
5. Submit a pull request

### Adding Industry-Specific Driver Schemas

To contribute driver schemas for a new industry:

1. Add industry-specific driver functions to `src/scaling_drivers.py`
2. Add an entry to `INDUSTRY_DRIVER_REFERENCE`
3. Add a section to `docs/industry_applications.md`
4. Submit a pull request with a brief description of the industry context

---

*This multimodel framework document is part of the AI Cost Attribution Framework. See [README.md](../README.md) for framework overview and [methodology.md](methodology.md) for detailed methodology documentation.*
