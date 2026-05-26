from __future__ import annotations

from typing import Any

import pandas as pd


def detect_anomalies(metrics: pd.DataFrame, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Detect simple business anomalies using configurable thresholds."""
    thresholds = config["anomaly_detection"]
    anomalies: list[dict[str, Any]] = []
    df = metrics.sort_values("month").copy()

    for _, row in df.iterrows():
        month = int(row["month"])
        if float(row["churn_rate"]) >= float(thresholds["churn_rate_high_threshold"]):
            anomalies.append(
                {
                    "month": month,
                    "type": "high_churn_rate",
                    "value": round(float(row["churn_rate"]), 4),
                    "message": f"Month {month}: churn rate is above threshold.",
                }
            )

    for idx in range(1, len(df)):
        current = df.iloc[idx]
        previous = df.iloc[idx - 1]
        month = int(current["month"])

        previous_revenue = float(previous["monthly_revenue"])
        current_revenue = float(current["monthly_revenue"])
        if previous_revenue > 0:
            revenue_change = (current_revenue - previous_revenue) / previous_revenue
            if revenue_change <= -float(thresholds["revenue_drop_threshold_pct"]):
                anomalies.append(
                    {
                        "month": month,
                        "type": "sharp_revenue_drop",
                        "value": round(float(revenue_change), 4),
                        "message": f"Month {month}: revenue dropped sharply versus previous month.",
                    }
                )

        previous_arpu = float(previous["arpu"])
        current_arpu = float(current["arpu"])
        if previous_arpu > 0:
            arpu_change = (current_arpu - previous_arpu) / previous_arpu
            if abs(arpu_change) >= float(thresholds["arpu_change_threshold_pct"]):
                anomalies.append(
                    {
                        "month": month,
                        "type": "significant_arpu_change",
                        "value": round(float(arpu_change), 4),
                        "message": f"Month {month}: ARPU changed significantly versus previous month.",
                    }
                )

    return anomalies
