# Official OpenSPG and KAG runtime

> Status: Retired historical record. The executable runtime and referenced lifecycle scripts were
> removed by [ADR 0006](../adr/0006-retire-openspg-runtime-and-fix-reason-port.md).

## Runtime authority

Tidewise Reason consumes the official
`spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server:latest` image as its sole OpenSPG/KAG
Server release. This repository does not compile upstream source, publish a derivative Server
image, replace the executable JAR, or replace the KAG wheel bundled in that image.

The `latest` tag is intentionally mutable. `scripts/start.sh` pulls it before starting the
service, and `scripts/verify-runtime.sh` prints the resolved repository digest so an evaluation run
can be traced to the artifact that actually ran.

## Deployment contract

- Compose project: `tidewise-app`.
- Service: `server`.
- Container: `reason-server`.
- Network: external `tidewise-local`.
- Middleware: independently operated MySQL, Neo4j and MinIO from `tidewise-infra`.
- Published Web port: loopback-only `127.0.0.1:8887`.

Lifecycle commands remain service-scoped:

```bash
./scripts/start.sh
./scripts/verify-runtime.sh
./scripts/stop.sh
```

No command in this repository may run an unscoped `docker compose down` or
`--remove-orphans` against the shared application project.

## Extension boundary

The official image remains unmodified. Tidewise-owned extensions should use one of these seams:

- SPG Schema and KGDSL submitted through the public OpenSPG APIs;
- Graph, search, builder, reasoner and scheduler public APIs through KNEXT;
- KAG pipeline configuration and public Builder/Solver interfaces;
- a separate Tidewise process or sidecar that implements custom Scanner, Extractor, Retriever,
  Planner, Executor, Generator, Prompt or MCP/HTTP adapters.

One compatibility override is approved for the bundled KAG runtime: Compose bind-mounts a
corrected `kag_thinker.yaml` as a read-only single-file replacement. The planner bundled in the
official image requires `rewrite_prompt` while the bundled pipeline configuration omits it. The
bundled `kag_clarification` prompt also leaves Action numbering implicit while the parser accepts
only `ActionN:` labels, causing generic models to produce plans that fail before retrieval. The
override reuses the already registered `default_rewrite_sub_task_query` and
`default_logic_form_plan` prompts. The configured generic DeepSeek model also does not emit the
KAG-Thinker `<search>` protocol expected by `kag_model_hybrid_retrieval_executor`, so the override
retains `KAGModelPlanner` for multi-step planning and selects the bundled
`kag_hybrid_retrieval_executor` to execute each retrieval step. Its optional per-step LLM summary
is disabled because the final generator performs answer synthesis. This is a generic-model
compatibility mode, not the full iterative KAG-Thinker search protocol. It does not replace or
modify the image, executable JAR or KAG wheel. Remove the compatibility substitutions after a
protocol-compatible model or an official matching pipeline is available.

An extension that requires replacing the KAG package inside `openspg-server` is outside this
runtime policy. If an upstream extension must appear as a selectable component in the official
product UI, either wait for an official image containing it or run the extension externally and
integrate through public APIs.

## Verification

Verification checks that Compose resolves only the official image, the running container uses the
locally pulled official image ID, the Web health/page endpoints respond, the bundled KAG and KNEXT
CLIs load, and the bundled KAG distribution can be imported. It does not patch or certify
individual upstream pipeline configurations.

The verification script also checks that the effective `kag_thinker_pipeline` declares both the
`default_rewrite_sub_task_query` prompt required by the bundled `KAGModelPlanner` and the numbered
logic-form planning prompt expected by its parser. It also checks that retrieval steps use the
bundled standard KAG hybrid executor required by the generic-model compatibility mode.
