import json
from pathlib import Path

from analysis_models import AnalysisArtifact
from runtime import DemoError, ErrorCode, REPO_ROOT


class ArtifactStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or REPO_ROOT / ".runtime" / "graphiti-demo"
        self.context_path = self.root / "analysis-context.json"
        self.result_path = self.root / "analysis-result.json"
        self.invalid_result_path = self.root / "analysis-invalid.json"

    def clear_all(self) -> None:
        for path in (self.context_path, self.result_path, self.invalid_result_path):
            path.unlink(missing_ok=True)

    def invalidate_result(self) -> None:
        self.result_path.unlink(missing_ok=True)
        self.invalid_result_path.unlink(missing_ok=True)

    def write_context(self, context: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.invalidate_result()
        self.context_path.write_text(
            json.dumps(context, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8",
        )

    def read_context(self) -> dict:
        if not self.context_path.is_file():
            raise DemoError(ErrorCode.GRAPH_STATE_INVALID, "analysis context is missing")
        try:
            return json.loads(self.context_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "analysis context is invalid") from None

    def write_result(self, artifact: AnalysisArtifact) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.invalid_result_path.unlink(missing_ok=True)
        self.result_path.write_text(artifact.model_dump_json(indent=2), encoding="utf-8")

    def write_invalid_result(self, raw_result: str) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self.result_path.unlink(missing_ok=True)
        self.invalid_result_path.write_text(raw_result, encoding="utf-8")

    def read_result(self) -> AnalysisArtifact:
        if not self.result_path.is_file():
            raise DemoError(ErrorCode.GRAPH_STATE_INVALID, "analysis result is missing")
        try:
            return AnalysisArtifact.model_validate_json(self.result_path.read_text(encoding="utf-8"))
        except Exception:
            raise DemoError(ErrorCode.ANALYSIS_INVALID, "analysis result is invalid") from None
