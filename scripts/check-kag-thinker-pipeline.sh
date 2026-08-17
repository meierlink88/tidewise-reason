#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" exec -T \
  -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 \
  server python - <<'PY'
import kag.solver
from kag.interface import PlannerABC
from kag.solver.main_solver import get_pipeline_conf

pipeline_config = get_pipeline_conf(
    "kag_thinker_pipeline",
    {"chat_llm": {"type": "openai"}, "retrievers": []},
)
planner_config = pipeline_config["planner"]
assert planner_config["type"] == "kag_model_planner"
assert "rewrite_prompt" not in planner_config
planner_config["llm"] = None
planner = PlannerABC.from_config(planner_config)

assert planner.__class__.__name__ == "KAGModelPlanner"
assert planner.system_prompt.__class__.__name__ == "KagSystemPrompt"
assert planner.clarification_prompt.__class__.__name__ == "KagClarificationPrompt"
print("kag_thinker_pipeline planner configuration is valid")
PY
