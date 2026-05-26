import pandas as pd

from src.pipeline.metrics import calculate_monthly_metrics


def test_calculate_monthly_metrics_known_input():
    data = pd.DataFrame(
        [
            {"user_id": 1, "month": 1, "payment_status": "paid", "amount_paid": 10.0, "is_active": True},
            {"user_id": 2, "month": 1, "payment_status": "paid", "amount_paid": 20.0, "is_active": True},
            {"user_id": 1, "month": 2, "payment_status": "paid", "amount_paid": 10.0, "is_active": True},
            {"user_id": 2, "month": 2, "payment_status": "failed", "amount_paid": 0.0, "is_active": False},
        ]
    )

    metrics = calculate_monthly_metrics(data)

    month_1 = metrics[metrics["month"] == 1].iloc[0]
    month_2 = metrics[metrics["month"] == 2].iloc[0]

    assert month_1["active_users"] == 2
    assert month_1["paid_users"] == 2
    assert month_1["monthly_revenue"] == 30.0
    assert month_1["churned_users"] == 0
    assert month_1["churn_rate"] == 0.0
    assert month_1["arpu"] == 15.0

    assert month_2["active_users"] == 1
    assert month_2["paid_users"] == 1
    assert month_2["monthly_revenue"] == 10.0
    assert month_2["churned_users"] == 1
    assert month_2["churn_rate"] == 0.5
    assert month_2["arpu"] == 10.0
