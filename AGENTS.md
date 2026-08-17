# AGENTS.md

This repository owns the local OpenSPG + KAG evaluation environment.

- Keep the local Docker Compose project name `tidewise-app`, service name `server`, and fixed local
  container name `reason-server`.
- Reuse the external `tidewise-local` network and the independently operated MySQL, Neo4j and
  MinIO services from `tidewise-infra`; do not provision middleware in this repository.
- Use service-scoped lifecycle commands. Never run unscoped `docker compose down` or
  `--remove-orphans` against the shared application project.
- Follow the official OpenSPG/KAG topology and use
  `spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server:latest` as the sole Server runtime
  release. Do not build or inject an OpenSPG JAR or KAG wheel in this repository.
- Keep runtime source checkouts, Python environments, data and credentials out of Git.
- Bind local evaluation ports to loopback by default.
- Do not treat the bundled demo credentials or Compose file as production configuration.
- Verify changes through the Web endpoint and the KAG/KNEXT CLIs.
