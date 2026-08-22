# AGENTS.md

This repository owns local reasoning-engine evaluations and their dedicated Neo4j provider.

- Keep the legacy OpenSPG + KAG Compose project name `tidewise-app`, service name `server`, and fixed
  local container name `reason-server` so the evaluation remains reversibly startable.
- Keep the Graphiti Neo4j provider in the dedicated `tidewise-reasoning` Compose project, service
  name `neo4j`, and fixed container name `reason-graphiti-neo4j`.
- Reuse the external `tidewise-local` network. MySQL and MinIO remain independently operated by
  `tidewise-infra`; only the reasoning-specific local Neo4j lifecycle belongs here.
- Use service-scoped lifecycle commands. Never run unscoped `docker compose down` or
  `--remove-orphans` against a shared project.
- Follow the official OpenSPG/KAG topology and use
  `spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server:latest` as the sole Server runtime
  release. Do not build or inject an OpenSPG JAR or KAG wheel in this repository.
- Pin Graphiti and Neo4j runtime versions. Do not use floating tags for the Graphiti evaluation.
- Never remove reasoning data volumes without explicit user authorization.
- Keep runtime source checkouts, Python environments, data and credentials out of Git.
- Bind local evaluation ports to loopback by default.
- Do not treat the bundled demo credentials or Compose file as production configuration.
- Verify OpenSPG changes through the Web endpoint and KAG/KNEXT CLIs; verify Graphiti through its
  Python API, Neo4j Browser and executable demo checks.
