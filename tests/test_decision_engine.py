from src.agent.decision_engine import AgentState, decide_next_action


def test_decision_engine_initial_state():
    assert decide_next_action(AgentState()) == "generate_data"


def test_decision_engine_after_data_generated():
    state = AgentState(data_generated=True)
    assert decide_next_action(state) == "calculate_metrics"


def test_decision_engine_halts_on_quality_failure():
    state = AgentState(
        data_generated=True,
        metrics_calculated=True,
        quality_checked=True,
        quality_failed=True,
    )
    assert decide_next_action(state) == "halt_with_error"


def test_decision_engine_done():
    state = AgentState(
        data_generated=True,
        metrics_calculated=True,
        quality_checked=True,
        quality_failed=False,
        anomalies_checked=True,
        report_generated=True,
    )
    assert decide_next_action(state) == "done"
