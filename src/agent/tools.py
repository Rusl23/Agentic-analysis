from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from src.pipeline.anomaly_detector import detect_anomalies as _detect_anomalies
from src.pipeline.generate_data import generate_subscription_data
from src.pipeline.metrics import calculate_monthly_metrics
from src.pipeline.quality_checks import run_quality_checks as _run_quality_checks
from src.reporting.report_builder import build_report


class AgentTools:
    """Tool registry used by the orchestrator."""

    def __init__(self, config: dict[str, Any], project_root: str | Path):
        self.config = config
        self.project_root = Path(project_root)
        self.data_path = self.project_root / "data" / "subscription_user_months.csv"
        self.metrics_path = self.project_root / "data" / "monthly_metrics.csv"
        self.quality_path = self.project_root / "data" / "quality_checks_results.json"
        self.report_path = self.project_root / "reports" / "churn_revenue_report.md"

    def generate_data(self) -> pd.DataFrame:
        return generate_subscription_data(self.config, self.data_path)

    def calculate_metrics(self, data: pd.DataFrame) -> pd.DataFrame:
        return calculate_monthly_metrics(data, self.metrics_path)

    def run_quality_checks(self, data: pd.DataFrame, metrics: pd.DataFrame) -> dict[str, Any]:
        return _run_quality_checks(data, metrics, self.config, self.quality_path)

    def detect_anomalies(self, metrics: pd.DataFrame) -> list[dict[str, Any]]:
        return _detect_anomalies(metrics, self.config)

    def generate_report(
        self,
        metrics: pd.DataFrame,
        quality_result: dict[str, Any],
        anomalies: list[dict[str, Any]],
        mode: str,
    ) -> str:
        model = self.config.get("agent", {}).get("openai_model", "gpt-4o-mini")
        return build_report(metrics, quality_result, anomalies, self.report_path, mode=mode, model=model)
