from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class GuardrailError(RuntimeError):
    """Raised when an agent guardrail fails."""


def ensure_file_exists(path: str | Path, label: str) -> None:
    if not Path(path).exists():
        raise GuardrailError(f"Expected {label} file does not exist: {path}")


def ensure_dataframe_not_empty(df: pd.DataFrame, label: str) -> None:
    if df.empty:
        raise GuardrailError(f"{label} dataframe is empty")


def ensure_quality_passed(quality_result: dict[str, Any]) -> None:
    if not quality_result.get("passed", False):
        failed = [check["check"] for check in quality_result.get("checks", []) if not check.get("passed")]
        raise GuardrailError(f"Quality checks failed: {failed}")


def ensure_report_sections(report_text: str) -> None:
    normalized_report = report_text.lower()
    required_sections = [
        "Executive summary",
        "Monthly revenue trend",
        "Churn trend",
        "ARPU trend",
        "Data quality checks",
        "Business interpretation",
    ]
    missing = [section for section in required_sections if section.lower() not in normalized_report]
    if missing:
        raise GuardrailError(f"Report is missing required sections: {missing}")
