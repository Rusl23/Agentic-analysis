from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_COLUMNS = [
    "user_id",
    "month",
    "plan",
    "monthly_price",
    "payment_status",
    "amount_paid",
    "is_active",
]


def _result(name: str, passed: bool, details: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "details": details}


def run_quality_checks(
    data: pd.DataFrame,
    metrics: pd.DataFrame,
    config: dict[str, Any],
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    """Run data and metric validation checks."""
    checks: list[dict[str, Any]] = []

    required_present = set(REQUIRED_COLUMNS).issubset(data.columns)
    checks.append(_result("required_columns_exist", required_present, f"Required columns: {REQUIRED_COLUMNS}"))

    if not required_present:
        result = {"passed": False, "checks": checks}
        _write_json(result, output_path)
        return result

    null_count = int(data[REQUIRED_COLUMNS].isna().sum().sum())
    checks.append(_result("no_nulls_in_required_fields", null_count == 0, f"Null values found: {null_count}"))

    unique_users = int(data["user_id"].nunique())
    expected_users = int(config["cohort_size"])
    checks.append(_result("user_count_is_correct", unique_users == expected_users, f"Unique users: {unique_users}, expected: {expected_users}"))

    months = sorted(data["month"].unique().tolist())
    expected_months = list(range(1, int(config["months"]) + 1))
    checks.append(_result("month_range_is_complete", months == expected_months, f"Months found: {months}"))

    duplicated_user_months = int(data.duplicated(["user_id", "month"]).sum())
    checks.append(_result("one_row_per_user_per_month", duplicated_user_months == 0, f"Duplicates: {duplicated_user_months}"))

    invalid_statuses = sorted(set(data["payment_status"]) - {"paid", "failed"})
    checks.append(_result("payment_statuses_are_valid", len(invalid_statuses) == 0, f"Invalid statuses: {invalid_statuses}"))

    valid_plans = set(config["plans"].keys())
    invalid_plans = sorted(set(data["plan"]) - valid_plans)
    checks.append(_result("plans_are_valid", len(invalid_plans) == 0, f"Invalid plans: {invalid_plans}"))

    negative_payments = int((data["amount_paid"] < 0).sum())
    checks.append(_result("no_negative_payments", negative_payments == 0, f"Negative payments: {negative_payments}"))

    failed_positive_amount = int(((data["payment_status"] == "failed") & (data["amount_paid"] != 0)).sum())
    checks.append(_result("failed_payments_have_zero_amount", failed_positive_amount == 0, f"Failed rows with non-zero amount: {failed_positive_amount}"))

    paid_non_positive_amount = int(((data["payment_status"] == "paid") & (data["amount_paid"] <= 0)).sum())
    checks.append(_result("paid_payments_have_positive_amount", paid_non_positive_amount == 0, f"Paid rows with non-positive amount: {paid_non_positive_amount}"))

    inactive_revenue_rows = int(((~data["is_active"].astype(bool)) & (data["amount_paid"] != 0)).sum())
    checks.append(_result("inactive_users_have_zero_revenue", inactive_revenue_rows == 0, f"Inactive rows with non-zero revenue: {inactive_revenue_rows}"))

    paid_le_active = bool((metrics["paid_users"] <= metrics["active_users"]).all())
    checks.append(_result("paid_users_do_not_exceed_active_users", paid_le_active, "paid_users <= active_users for all months"))

    raw_revenue = data.groupby("month")["amount_paid"].sum().round(2).reset_index(name="raw_revenue")
    merged = metrics[["month", "monthly_revenue"]].merge(raw_revenue, on="month", how="left")
    revenue_diff = (merged["monthly_revenue"].round(2) - merged["raw_revenue"].round(2)).abs().max()
    checks.append(_result("revenue_reconciliation_passes", revenue_diff < 0.01, f"Max revenue diff: {revenue_diff}"))

    metric_validations = [
        ("churned_users_non_negative", bool((metrics["churned_users"] >= 0).all())),
        ("churn_rate_between_0_and_1", bool(((metrics["churn_rate"] >= 0) & (metrics["churn_rate"] <= 1)).all())),
        ("arpu_non_negative", bool((metrics["arpu"] >= 0).all())),
        ("monthly_revenue_non_negative", bool((metrics["monthly_revenue"] >= 0).all())),
    ]
    for name, passed in metric_validations:
        checks.append(_result(name, passed, "Metric validation"))

    result = {"passed": all(check["passed"] for check in checks), "checks": checks}
    _write_json(result, output_path)
    return result


def _write_json(result: dict[str, Any], output_path: str | Path | None) -> None:
    if output_path is None:
        return
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
