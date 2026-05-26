from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.agent.decision_engine import AgentState, decide_next_action
from src.agent.guardrails import (
    ensure_dataframe_not_empty,
    ensure_file_exists,
    ensure_quality_passed,
    ensure_report_sections,
)
from src.agent.tools import AgentTools


class ReportingAgent:
    """Lightweight state-based reporting agent."""

    def __init__(self, config: dict[str, Any], project_root: str | Path, mode: str = "deterministic"):
        self.config = config
        self.project_root = Path(project_root)
        self.mode = mode
        self.tools = AgentTools(config, project_root)
        self.state = AgentState()
        self.log: list[dict[str, Any]] = []
        self.data: pd.DataFrame | None = None
        self.metrics: pd.DataFrame | None = None
        self.quality_result: dict[str, Any] | None = None
        self.anomalies: list[dict[str, Any]] = []

    def run(self) -> dict[str, Any]:
        self._prepare_outputs()
        max_tool_calls = int(self.config.get("agent", {}).get("max_tool_calls", 10))
        tool_calls = 0

        while True:
            action = decide_next_action(self.state)
            if action == "done":
                self._log(action, "Workflow completed")
                break
            if action == "halt_with_error":
                self._log(action, "Workflow halted because quality checks failed")
                break
            if tool_calls >= max_tool_calls:
                raise RuntimeError(f"Maximum tool calls exceeded: {max_tool_calls}")

            self._execute(action)
            tool_calls += 1

        status = "failed" if self.state.quality_failed else "success"
        run_result = {
            "status": status,
            "mode": self.mode,
            "tool_calls": tool_calls,
            "state": self.state.__dict__,
            "log": self.log,
        }
        self._write_log(run_result)
        return run_result

    def _execute(self, action: str) -> None:
        if action == "generate_data":
            self.data = self.tools.generate_data()
            ensure_dataframe_not_empty(self.data, "subscription data")
            ensure_file_exists(self.tools.data_path, "subscription data")
            self.state.data_generated = True
            self._log(action, f"Generated {len(self.data)} user-month rows")
            return

        if action == "calculate_metrics":
            assert self.data is not None
            self.metrics = self.tools.calculate_metrics(self.data)
            ensure_dataframe_not_empty(self.metrics, "monthly metrics")
            ensure_file_exists(self.tools.metrics_path, "monthly metrics")
            self.state.metrics_calculated = True
            self._log(action, f"Calculated metrics for {len(self.metrics)} months")
            return

        if action == "run_quality_checks":
            assert self.data is not None and self.metrics is not None
            self.quality_result = self.tools.run_quality_checks(self.data, self.metrics)
            ensure_file_exists(self.tools.quality_path, "quality checks")
            self.state.quality_checked = True
            self.state.quality_failed = not bool(self.quality_result.get("passed"))
            if self.state.quality_failed:
                self.tools.generate_failure_report(self.quality_result)
                ensure_file_exists(self.tools.report_path, "failure report")
                self._log(action, "Quality checks failed")
            else:
                ensure_quality_passed(self.quality_result)
                self._log(action, "Quality checks passed")
            return

        if action == "detect_anomalies":
            assert self.metrics is not None
            self.anomalies = self.tools.detect_anomalies(self.metrics)
            self.state.anomalies_checked = True
            self._log(action, f"Detected {len(self.anomalies)} anomalies")
            return

        if action == "generate_report":
            assert self.metrics is not None and self.quality_result is not None
            report_text = self.tools.generate_report(self.metrics, self.quality_result, self.anomalies, self.mode)
            ensure_file_exists(self.tools.report_path, "final report")
            ensure_report_sections(report_text)
            self.state.report_generated = True
            self._log(action, f"Generated report: {self.tools.report_path}")
            return

        raise ValueError(f"Unknown action: {action}")

    def _prepare_outputs(self) -> None:
        """Remove stale report artifacts before a full-refresh run."""
        self.tools.report_path.unlink(missing_ok=True)

    def _log(self, action: str, message: str) -> None:
        self.log.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": action,
                "message": message,
                "state": self.state.__dict__.copy(),
            }
        )

    def _write_log(self, run_result: dict[str, Any]) -> None:
        path = self.project_root / "reports" / "agent_run_log.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(run_result, indent=2), encoding="utf-8")
