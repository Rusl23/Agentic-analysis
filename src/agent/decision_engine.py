from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentState:
    data_generated: bool = False
    metrics_calculated: bool = False
    quality_checked: bool = False
    quality_failed: bool = False
    anomalies_checked: bool = False
    report_generated: bool = False


def decide_next_action(state: AgentState) -> str:
    """Choose the next tool based on the current workflow state."""
    if not state.data_generated:
        return "generate_data"
    if not state.metrics_calculated:
        return "calculate_metrics"
    if not state.quality_checked:
        return "run_quality_checks"
    if state.quality_failed:
        return "halt_with_error"
    if not state.anomalies_checked:
        return "detect_anomalies"
    if not state.report_generated:
        return "generate_report"
    return "done"
