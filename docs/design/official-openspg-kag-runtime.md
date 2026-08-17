# Official OpenSPG and KAG runtime

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

An extension that requires replacing the KAG package inside `openspg-server` is outside this
runtime policy. If an upstream extension must appear as a selectable component in the official
product UI, either wait for an official image containing it or run the extension externally and
integrate through public APIs.

## Verification

Verification checks that Compose resolves only the official image, the running container uses the
locally pulled official image ID, the Web health/page endpoints respond, the bundled KAG and KNEXT
CLIs load, and the bundled KAG distribution can be imported. It does not patch or certify
individual upstream pipeline configurations.

At the time this policy was adopted, the resolved official image contains a
`kag_thinker_pipeline` configuration without the `rewrite_prompt` required by its bundled
`KAGModelPlanner`. The former local runtime patched and tested that seam; the official-only policy
deliberately does not. Use another supported public Solver pipeline for programmatic integration,
or wait for an official image that fixes the mismatch.
