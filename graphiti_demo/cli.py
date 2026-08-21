import argparse
import asyncio
import json
import sys

from artifact_store import ArtifactStore
from graphiti_adapter import GraphitiEvaluationAdapter
from pipeline import ReasoningDemoPipeline
from providers import AnalysisLLMAdapter
from runtime import DemoError, ErrorCode, EvidenceClient, load_config


async def main() -> None:
    parser = argparse.ArgumentParser(description="Graphiti industry-chain reasoning demo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    seed_parser = subparsers.add_parser("seed")
    seed_parser.add_argument(
        "--reset",
        action="store_true",
        help="clear every node in the dedicated local evaluation database before rebuilding",
    )
    subparsers.add_parser("evidence-smoke")
    subparsers.add_parser("retrieve")
    subparsers.add_parser("analyze")
    subparsers.add_parser("inspect")
    subparsers.add_parser("verify")
    args = parser.parse_args()
    config = load_config()
    pipeline = ReasoningDemoPipeline(
        evidence_source=EvidenceClient(config),
        graph_memory=GraphitiEvaluationAdapter(config),
        analysis_model=AnalysisLLMAdapter(config),
        artifacts=ArtifactStore(),
    )

    if args.command == "seed":
        output = await pipeline.seed(args.reset)
    elif args.command == "evidence-smoke":
        output = await pipeline.evidence_smoke()
    elif args.command == "retrieve":
        output = await pipeline.retrieve()
    elif args.command == "analyze":
        output = await pipeline.analyze()
    elif args.command == "inspect":
        output = await pipeline.inspect()
    else:
        output = await pipeline.verify()
    print(json.dumps(output, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except DemoError as exc:
        print(json.dumps({"error": exc.code, "message": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2) from None
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": ErrorCode.PROVIDER_FAILED,
                    "message": f"provider operation failed ({exc.__class__.__name__})",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        raise SystemExit(3) from None
