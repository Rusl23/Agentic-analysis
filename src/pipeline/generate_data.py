from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def generate_subscription_data(config: dict[str, Any], output_path: str | Path) -> pd.DataFrame:
    """Generate synthetic subscription user-month data.

    Assumptions:
    - Single cohort acquired in month 1.
    - No new users after month 1.
    - Once churned, a user stays inactive.
    - Failed payments produce zero revenue.
    """
    rng = np.random.default_rng(config["seed"])
    cohort_size = int(config["cohort_size"])
    months = int(config["months"])

    plan_names = list(config["plans"].keys())
    plan_prices = config["plans"]
    plan_distribution = [config["plan_distribution"][plan] for plan in plan_names]

    user_ids = np.arange(1, cohort_size + 1)
    user_plans = rng.choice(plan_names, size=cohort_size, p=plan_distribution)

    active_flags = np.ones(cohort_size, dtype=bool)
    rows: list[dict[str, Any]] = []

    for month in range(1, months + 1):
        if month > 1:
            churn_probability = (
                float(config["churn"]["base_rate"])
                + float(config["churn"]["monthly_increase"]) * (month - 2)
            )
            churn_probability = min(max(churn_probability, 0.0), 1.0)
            churn_events = rng.random(cohort_size) < churn_probability
            active_flags = active_flags & ~churn_events

        for user_id, plan, is_active in zip(user_ids, user_plans, active_flags):
            monthly_price = float(plan_prices[plan])
            if is_active:
                payment_failed = rng.random() < float(config["payment_failure_rate"])
                payment_status = "failed" if payment_failed else "paid"
                amount_paid = 0.0 if payment_failed else monthly_price
            else:
                payment_status = "failed"
                amount_paid = 0.0

            rows.append(
                {
                    "user_id": int(user_id),
                    "month": int(month),
                    "plan": plan,
                    "monthly_price": monthly_price,
                    "payment_status": payment_status,
                    "amount_paid": round(float(amount_paid), 2),
                    "is_active": bool(is_active),
                }
            )

    df = pd.DataFrame(rows)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return df
