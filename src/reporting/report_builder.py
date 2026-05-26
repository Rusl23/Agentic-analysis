from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

from src.reporting.prompts import REPORT_PROMPT, SYSTEM_PROMPT


def build_report(
    metrics: pd.DataFrame,
    quality_result: dict[str, Any],
    anomalies: list[dict[str, Any]],
    output_path: str | Path,
    mode: str = "deterministic",
    model: str = "gpt-4o-mini",
) -> str:
    """Build final markdown report.

    LLM mode is optional. If unavailable, deterministic mode is used.
    """
    report_text: str
    if mode == "llm" and os.getenv("OPENAI_API_KEY"):
        try:
            report_text = _build_llm_report(metrics, quality_result, anomalies, model=model)
        except Exception:
            report_text = _build_deterministic_report(metrics, quality_result, anomalies, fallback_used=True)
    else:
        report_text = _build_deterministic_report(metrics, quality_result, anomalies, fallback_used=(mode == "llm"))

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report_text, encoding="utf-8")
    return report_text


def _build_llm_report(
    metrics: pd.DataFrame,
    quality_result: dict[str, Any],
    anomalies: list[dict[str, Any]],
    model: str,
) -> str:
    # Optional path. The project remains fully reproducible without it.
    from openai import OpenAI

    client = OpenAI()
    user_content = (
        f"{REPORT_PROMPT}\n\n"
        f"Monthly metrics:\n{metrics.to_markdown(index=False)}\n\n"
        f"Quality result:\n{quality_result}\n\n"
        f"Anomalies:\n{anomalies}"
    )
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", model),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def _build_deterministic_report(
    metrics: pd.DataFrame,
    quality_result: dict[str, Any],
    anomalies: list[dict[str, Any]],
    fallback_used: bool = False,
) -> str:
    df = metrics.sort_values("month")
    first = df.iloc[0]
    last = df.iloc[-1]
    peak_revenue = df.loc[df["monthly_revenue"].idxmax()]
    min_revenue = df.loc[df["monthly_revenue"].idxmin()]
    highest_churn = df.loc[df["churn_rate"].idxmax()]
    lowest_churn_after_m1 = df[df["month"] > 1].loc[df[df["month"] > 1]["churn_rate"].idxmin()]
    highest_arpu = df.loc[df["arpu"].idxmax()]
    lowest_arpu = df.loc[df["arpu"].idxmin()]

    revenue_change = float(last["monthly_revenue"] - first["monthly_revenue"])
    revenue_change_pct = revenue_change / float(first["monthly_revenue"]) if first["monthly_revenue"] else 0.0
    active_change = int(last["active_users"] - first["active_users"])

    quality_passed = quality_result.get("passed", False)
    failed_checks = [check for check in quality_result.get("checks", []) if not check.get("passed")]

    anomaly_lines = "\n".join(
        f"- Month {item['month']}: {item['type']} ({item['value']})"
        for item in anomalies
    ) or "- No major anomalies were detected using the configured thresholds."

    fallback_note = "\n\n_Note: LLM mode was requested but deterministic fallback was used._\n" if fallback_used else ""

    return f"""# Churn & Revenue Report

{fallback_note}
## 1. Executive summary

The cohort started with **{int(first['active_users'])} active users** and ended with **{int(last['active_users'])} active users**, a net change of **{active_change} users** over 12 months. Monthly revenue moved from **${float(first['monthly_revenue']):,.2f}** in month 1 to **${float(last['monthly_revenue']):,.2f}** in month 12, which is a **{revenue_change_pct:.1%}** change. The main driver of the decline is cumulative churn: fewer active users remain available to generate subscription revenue each month.

## 2. Monthly revenue trend

Revenue peaked in **month {int(peak_revenue['month'])}** at **${float(peak_revenue['monthly_revenue']):,.2f}** and reached its lowest value in **month {int(min_revenue['month'])}** at **${float(min_revenue['monthly_revenue']):,.2f}**. The overall trend is downward because the dataset models a closed cohort with no new user acquisition. Even when ARPU is relatively stable, the shrinking active user base reduces total monthly revenue.

## 3. Churn trend

The highest churn rate was observed in **month {int(highest_churn['month'])}** at **{float(highest_churn['churn_rate']):.2%}**. Excluding month 1, the lowest churn rate was observed in **month {int(lowest_churn_after_m1['month'])}** at **{float(lowest_churn_after_m1['churn_rate']):.2%}**. Churn generally increases over time because the synthetic data generation assumes a slightly rising monthly churn probability.

## 4. ARPU trend

ARPU was highest in **month {int(highest_arpu['month'])}** at **${float(highest_arpu['arpu']):.2f}** and lowest in **month {int(lowest_arpu['month'])}** at **${float(lowest_arpu['arpu']):.2f}**. Compared with total revenue, ARPU is more stable because plan distribution remains fixed and failed payments are relatively rare. Small ARPU movements are mainly caused by payment failures and changes in the remaining plan mix.

## 5. Data quality checks

Data quality status: **{'PASSED' if quality_passed else 'FAILED'}**.

Total checks executed: **{len(quality_result.get('checks', []))}**.
Failed checks: **{len(failed_checks)}**.

Anomaly summary:

{anomaly_lines}

## 6. Business interpretation

1. **Revenue decline is primarily retention-driven.** Since no new users are added after month 1, every churned user permanently reduces future revenue potential.
2. **Churn control would have the highest impact.** Improving retention in later months should directly slow the revenue decline curve.
3. **ARPU appears comparatively stable.** This suggests the main business issue is not pricing or monetization per active user, but the shrinking active user base.

Recommended next steps:

- investigate churn drivers by plan and tenure;
- test lifecycle campaigns before the months with the highest churn;
- monitor failed payments separately from true churn to identify recoverable revenue.
"""
