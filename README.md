# AI Agent for Churn & Revenue Report

A lightweight reporting agent for a consumer fintech subscription company.

The project generates synthetic subscription data for 1,000 users over 12 months, calculates monthly revenue/churn metrics, validates data quality, detects simple anomalies, and produces a short business report.

The goal is not to build a complex AI system, but to demonstrate a clear and reproducible agentic workflow where deterministic calculations are combined with structured report generation.

---

## Repository structure

```text
churn_revenue_agent/
├── README.md
├── requirements.txt
├── config.yaml
├── src/
│   ├── main.py
│   ├── agent/
│   │   ├── orchestrator.py
│   │   ├── decision_engine.py
│   │   ├── tools.py
│   │   └── guardrails.py
│   ├── pipeline/
│   │   ├── generate_data.py
│   │   ├── metrics.py
│   │   ├── quality_checks.py
│   │   └── anomaly_detector.py
│   └── reporting/
│       ├── report_builder.py
│       └── prompts.py
├── tests/
│   ├── test_metrics.py
│   ├── test_quality_checks.py
│   └── test_decision_engine.py
├── data/
│   ├── subscription_user_months.csv
│   ├── monthly_metrics.csv
│   └── quality_checks_results.json
└── reports/
    ├── churn_revenue_report.md
    └── agent_run_log.json
```

---

## How to run

```bash
git clone <repo-url>
cd churn_revenue_agent

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
python src/main.py
```

The default mode is deterministic and does not require an API key.

Optional LLM-assisted mode:

```bash
cp .env.example .env
# add your OpenAI API key to .env
python src/main.py --mode llm
```

The LLM model can be configured in `config.yaml` via `agent.openai_model` or overridden with `OPENAI_MODEL` in `.env`.

If the LLM call fails or the API key is missing, the agent falls back to deterministic report generation.

---

## Outputs

Each run regenerates the following files:

```text
data/subscription_user_months.csv
data/monthly_metrics.csv
data/quality_checks_results.json
reports/churn_revenue_report.md
reports/agent_run_log.json
```

---

## Problem context

A consumer fintech company has a subscription-based business model.

In month 1, the company acquires 1,000 users. Over the next 12 months, some users continue paying while others churn.

The reporting agent answers the following business questions:

- how monthly revenue changes over time;
- how active users and churn evolve;
- how churn affects revenue;
- whether there are data quality issues or anomalies;
- what business conclusions can be made from the trends.

---

## Synthetic input data

The generated dataset contains one row per user per month.

Main fields:

| Column | Description |
|---|---|
| user_id | Unique user identifier |
| month | Month number from 1 to 12 |
| plan | Subscription plan |
| monthly_price | Price of the selected plan |
| payment_status | Payment result: `paid` or `failed` |
| amount_paid | Actual paid amount |
| is_active | Whether the user is active in the given month |

Subscription plans:

| Plan | Monthly price |
|---|---:|
| Basic | 9.99 |
| Plus | 19.99 |
| Premium | 29.99 |

---

## Metric definitions

The agent calculates the following metrics by month:

| Metric | Definition |
|---|---|
| active_users | Number of active users in the month |
| paid_users | Number of active users with successful payment |
| churned_users | Users active in the previous month but inactive in the current month |
| monthly_revenue | Sum of `amount_paid` in the month |
| churn_rate | `churned_users / active_users_previous_month` |
| arpu | `monthly_revenue / active_users` |

For month 1, `churn_rate = 0`, because there is no previous month.

---

## Agentic approach

This project uses a lightweight agentic workflow.

The agent is not responsible for inventing numbers or calculating metrics with an LLM. Instead, it orchestrates deterministic tools and validates every important step before producing the final report.

The agent performs the role of a reporting analyst:

1. generates or loads subscription data;
2. calculates monthly metrics;
3. runs data quality checks;
4. detects simple anomalies;
5. generates a structured business report;
6. writes an execution log.

---

## Agent architecture

The workflow is state-based.

```text
Agent state
    ↓
Decision engine selects next action
    ↓
Tool is executed
    ↓
Guardrails validate the result
    ↓
State is updated
    ↓
Final report is generated
```

Available tools:

| Tool | Purpose |
|---|---|
| generate_data | Generate synthetic user-month subscription data |
| calculate_metrics | Calculate revenue, churn, active users and ARPU |
| run_quality_checks | Validate input data and calculated metrics |
| detect_anomalies | Flag unusual revenue, churn or ARPU movements |
| generate_report | Build the final markdown report |

---

## Decision engine logic

The decision engine decides which step should be executed next based on the current state.

Simplified logic:

```python
def decide_next_action(state):
    if not state.data_generated:
        return "generate_data"

    if not state.metrics_calculated:
        return "calculate_metrics"

    if not state.quality_checked:
        return "run_quality_checks"

    if state.quality_failed:
        return "halt_with_error"

    if not state.anomalies_checked:
        return "detect_anomalies"

    if not state.report_generated:
        return "generate_report"

    return "done"
```

This makes the workflow explicit and easy to inspect.

---

## Where deterministic code is used

All numerical calculations are done with Python, pandas and numpy.

Deterministic code is used for:

- revenue aggregation;
- active user counts;
- paid user counts;
- churn calculation;
- churn rate calculation;
- ARPU calculation;
- data quality checks;
- anomaly flags.

This is intentional: financial and subscription metrics must be reproducible, testable and auditable.

The LLM, when enabled, is used only for narrative interpretation of already validated metrics.

---

## Report generation modes

The project supports two report modes.

### 1. Deterministic mode

Default mode.

```bash
python src/main.py
```

The report is generated with predefined templates and deterministic business logic.

No API key is required.

### 2. LLM-assisted mode

Optional mode.

```bash
python src/main.py --mode llm
```

In this mode, the LLM receives only validated metrics, anomaly flags and data quality results.

The LLM does not calculate metrics. It only helps phrase the business interpretation.

If the LLM call fails, the agent falls back to deterministic report generation.

---

## Prompts used in LLM mode

The LLM mode uses a constrained prompt.

```python
SYSTEM_PROMPT = """
You are a fintech subscription reporting analyst.

Use only the provided metrics, anomaly flags and data quality results.
Do not invent numbers.
Do not create claims that are not supported by the data.
Reference specific months when describing trends.
Keep the report concise and business-oriented.
"""
```

```python
REPORT_PROMPT = """
Given the monthly metrics table, anomaly flags and data quality results,
produce a short report with the following sections:

1. Executive summary
2. Monthly revenue trend
3. Churn trend
4. ARPU trend
5. Data quality checks
6. Business interpretation

Include 2-3 business conclusions.
"""
```

---

## Guardrails and data quality checks

The agent stops report generation if critical data checks fail.

Data quality checks include:

| Check | Expected result |
|---|---|
| Required columns exist | All required columns are present |
| No nulls in required fields | No missing values |
| User count is correct | Exactly 1,000 unique users |
| Month range is complete | Months 1–12 exist |
| One row per user per month | No duplicate user-month rows |
| Payment statuses are valid | Only `paid` or `failed` |
| Plans are valid | Only configured plans |
| No negative payments | `amount_paid >= 0` |
| Failed payments have zero amount | `failed` → `amount_paid = 0` |
| Paid payments have positive amount | `paid` → `amount_paid > 0` |
| Inactive users have zero revenue | inactive → `amount_paid = 0` |
| Paid users do not exceed active users | `paid_users <= active_users` |
| Revenue reconciliation passes | Raw revenue equals metrics revenue |

The agent also performs basic metric validation:

- churned users cannot be negative;
- churn rate must be between 0 and 1;
- ARPU cannot be negative;
- monthly revenue cannot be negative.

---

## Anomaly detection

The project includes simple anomaly detection.

The agent flags months where:

- revenue drops sharply compared with the previous month;
- churn rate is unusually high;
- ARPU changes significantly compared with the previous month.

The thresholds are configured in `config.yaml`.

The purpose is not advanced statistical modelling, but a simple analytical signal for the final business report.

---

## Agent run log

Each run creates:

```text
reports/agent_run_log.json
```

The log contains:

- executed steps;
- tool outputs summary;
- quality check status;
- anomaly status;
- report generation mode;
- final workflow status.

This makes the run traceable and easier to debug.

---

## Configuration

Example `config.yaml`:

```yaml
seed: 42
cohort_size: 1000
months: 12

plans:
  Basic: 9.99
  Plus: 19.99
  Premium: 29.99

plan_distribution:
  Basic: 0.55
  Plus: 0.30
  Premium: 0.15

churn:
  base_rate: 0.04
  monthly_increase: 0.008

payment_failure_rate: 0.03

anomaly_detection:
  revenue_drop_threshold_pct: 0.15
  churn_rate_high_threshold: 0.10
  arpu_change_threshold_pct: 0.10

agent:
  max_tool_calls: 10
  default_mode: deterministic
```

---

## Assumptions

The solution uses the following assumptions:

- the dataset represents a single cohort of 1,000 users;
- no new users are acquired after month 1;
- once a user churns, they do not reactivate;
- failed payment means zero revenue for that user-month;
- ARPU is calculated as revenue divided by active users;
- all calculations are monthly;
- random seed is fixed for reproducibility.

---

## Final report

The generated report contains:

1. Executive summary
2. Monthly revenue trend
3. Churn trend
4. ARPU trend
5. Data quality checks
6. Business interpretation

The report explains:

- how revenue changed over 12 months;
- which months had higher or lower churn;
- how churn affected revenue;
- whether anomalies were detected;
- 2–3 business conclusions.

---

## Running tests

```bash
pytest tests/ -v
```

Tests cover:

- metric calculations on controlled input data;
- churn logic;
- ARPU calculation;
- data quality checks;
- decision engine transitions;
- guardrail behavior on invalid data.

---

## Why this approach is useful

This approach combines the reliability of deterministic analytics code with the flexibility of an agentic reporting workflow.

Main advantages:

1. **Reproducibility** — fixed seed and deterministic calculations.
2. **Auditability** — all metrics are generated from CSV and validated.
3. **Safety** — the agent stops when critical checks fail.
4. **Clarity** — the workflow is explicit and easy to understand.
5. **Extensibility** — new tools can be added to the agent without rewriting the whole pipeline.
6. **Business usefulness** — the final output is not just a table, but a concise business interpretation.

---

## Acceptance criteria coverage

| Requirement | Covered by |
|---|---|
| Generate synthetic data | `generate_data.py` |
| Calculate revenue/churn/ARPU | `metrics.py` |
| Validate data and calculations | `quality_checks.py`, `guardrails.py` |
| Produce final report | `report_builder.py` |
| Explain agentic approach | README section “Agentic approach” |
| Reproducible execution | Fixed seed, config, deterministic mode |
| Tests | `tests/` |
