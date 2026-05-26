import pandas as pd

from src.pipeline.metrics import calculate_monthly_metrics
from src.pipeline.quality_checks import run_quality_checks
from src.reporting.report_builder import build_failure_report


CONFIG = {
    "cohort_size": 2,
    "months": 2,
    "plans": {"Basic": 9.99, "Plus": 19.99},
}


def test_quality_checks_pass_on_valid_data():
    data = pd.DataFrame(
        [
            {"user_id": 1, "month": 1, "plan": "Basic", "monthly_price": 9.99, "payment_status": "paid", "amount_paid": 9.99, "is_active": True},
            {"user_id": 2, "month": 1, "plan": "Plus", "monthly_price": 19.99, "payment_status": "paid", "amount_paid": 19.99, "is_active": True},
            {"user_id": 1, "month": 2, "plan": "Basic", "monthly_price": 9.99, "payment_status": "paid", "amount_paid": 9.99, "is_active": True},
            {"user_id": 2, "month": 2, "plan": "Plus", "monthly_price": 19.99, "payment_status": "failed", "amount_paid": 0.0, "is_active": False},
        ]
    )
    metrics = calculate_monthly_metrics(data)
    result = run_quality_checks(data, metrics, CONFIG)
    assert result["passed"] is True


def test_quality_checks_fail_on_negative_payment():
    data = pd.DataFrame(
        [
            {"user_id": 1, "month": 1, "plan": "Basic", "monthly_price": 9.99, "payment_status": "paid", "amount_paid": -1.0, "is_active": True},
            {"user_id": 2, "month": 1, "plan": "Plus", "monthly_price": 19.99, "payment_status": "paid", "amount_paid": 19.99, "is_active": True},
            {"user_id": 1, "month": 2, "plan": "Basic", "monthly_price": 9.99, "payment_status": "paid", "amount_paid": 9.99, "is_active": True},
            {"user_id": 2, "month": 2, "plan": "Plus", "monthly_price": 19.99, "payment_status": "failed", "amount_paid": 0.0, "is_active": False},
        ]
    )
    metrics = calculate_monthly_metrics(data)
    result = run_quality_checks(data, metrics, CONFIG)
    assert result["passed"] is False
    failed = [check["check"] for check in result["checks"] if not check["passed"]]
    assert "no_negative_payments" in failed


def test_failure_report_contains_failed_quality_checks(tmp_path):
    quality_result = {
        "passed": False,
        "checks": [
            {
                "check": "no_negative_payments",
                "passed": False,
                "details": "Negative payments: 1",
            },
            {
                "check": "month_range_is_complete",
                "passed": True,
                "details": "Months found: [1, 2]",
            },
        ],
    }
    output_path = tmp_path / "churn_revenue_report.md"

    report_text = build_failure_report(quality_result, output_path)

    assert output_path.exists()
    assert "FAILED" in report_text
    assert "Data quality checks failed" in report_text
    assert "no_negative_payments" in report_text
    assert "Negative payments: 1" in report_text
    assert "month_range_is_complete" not in report_text
