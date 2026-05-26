from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import yaml

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*args, **kwargs) -> bool:
        return False

from src.agent.orchestrator import ReportingAgent


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(description="Run the churn and revenue reporting agent")
    parser.add_argument("--mode", choices=["deterministic", "llm"], default=None)
    args = parser.parse_args()

    project_root = PROJECT_ROOT
    config = load_config(project_root / "config.yaml")
    mode = args.mode or config.get("agent", {}).get("default_mode", "deterministic")

    agent = ReportingAgent(config=config, project_root=project_root, mode=mode)
    result = agent.run()

    print(f"Agent run status: {result['status']}")
    print("Generated files:")
    print("- data/subscription_user_months.csv")
    print("- data/monthly_metrics.csv")
    print("- data/quality_checks_results.json")
    print("- reports/churn_revenue_report.md")
    print("- reports/agent_run_log.json")


if __name__ == "__main__":
    main()
