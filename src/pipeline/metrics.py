from __future__ import annotations

from pathlib import Path

import pandas as pd


def calculate_monthly_metrics(data: pd.DataFrame, output_path: str | Path | None = None) -> pd.DataFrame:
    """Calculate monthly active users, paid users, churn, revenue, churn rate and ARPU."""
    df = data.copy()
    df["is_active"] = df["is_active"].astype(bool)

    active_by_month = df[df["is_active"]].groupby("month")["user_id"].nunique()
    paid_by_month = df[(df["is_active"]) & (df["payment_status"] == "paid")].groupby("month")["user_id"].nunique()
    revenue_by_month = df.groupby("month")["amount_paid"].sum()

    months = sorted(df["month"].unique())
    rows = []
    previous_active_users: set[int] | None = None

    for month in months:
        current_active_users = set(df[(df["month"] == month) & (df["is_active"])] ["user_id"].unique())
        active_users = int(active_by_month.get(month, 0))
        paid_users = int(paid_by_month.get(month, 0))
        monthly_revenue = round(float(revenue_by_month.get(month, 0.0)), 2)

        if previous_active_users is None:
            churned_users = 0
            churn_rate = 0.0
        else:
            churned_users = len(previous_active_users - current_active_users)
            churn_rate = churned_users / len(previous_active_users) if previous_active_users else 0.0

        arpu = monthly_revenue / active_users if active_users else 0.0

        rows.append(
            {
                "month": int(month),
                "active_users": active_users,
                "paid_users": paid_users,
                "churned_users": int(churned_users),
                "monthly_revenue": monthly_revenue,
                "churn_rate": round(float(churn_rate), 4),
                "arpu": round(float(arpu), 2),
            }
        )
        previous_active_users = current_active_users

    metrics = pd.DataFrame(rows)
    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        metrics.to_csv(output_path, index=False)
    return metrics
