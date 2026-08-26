# AGENTS.md

This repository owns the Tidewise Reasoning Server and its dedicated Graphiti Neo4j provider.

- Keep the Reasoning Server and Graphiti Neo4j provider in the dedicated `tidewise-reasoning`
  Compose project. The services are `api` and `neo4j`, with fixed local container names
  `reason-service` and `reason-graphiti-neo4j`.
- Keep the Reasoning Server HTTP binding fixed at loopback-only `127.0.0.1:8890`; do not introduce
  an environment-variable port override.
- Reuse the external `tidewise-local` network. MySQL and MinIO remain independently operated by
  `tidewise-infra`; only the reasoning-specific local Neo4j lifecycle belongs here.
- Use service-scoped lifecycle commands. Never run unscoped `docker compose down` or
  `--remove-orphans` against a shared project.
- Pin Graphiti and Neo4j runtime versions. Do not use floating tags for the Graphiti evaluation.
- Never remove reasoning data volumes without explicit user authorization.
- Keep runtime source checkouts, Python environments, data and credentials out of Git.
- Bind local evaluation ports to loopback by default.
- Do not treat the bundled demo credentials or Compose file as production configuration.
- Verify Graphiti through its Python API, Neo4j Browser and executable checks. Verify the Reasoning
  Server through health, readiness, OpenAPI and authenticated API contracts.
