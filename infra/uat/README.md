# Reason UAT continuous delivery

Tidewise Reason UAT deploys only the official OpenSPG Server image, whose runtime bundles KAG, and
future Tidewise-owned Reasoning configuration or extensions. MySQL, Neo4j and MinIO are independent
infrastructure owned and deployed by `tidewise-ai`; this directory never installs, upgrades, clears,
backs up, restarts or rolls them back.

## Runtime topology

- Compose project: `tidewise-reason-uat`.
- Service: `server`.
- Container: `reason-server-uat`.
- Deployment root: `/opt/tidewise/reason-uat`.
- Shared external network: `tidewise-uat`.
- Web endpoint: office-allowlisted ECS port `0.0.0.0:8887`, reached at
  `http://123.60.99.198:8887`.
- MySQL: the external `mysql:3306` network alias.
- MinIO: the external `minio:9000` network alias.
- Neo4j: host-native Bolt through the `release-openspg-neo4j` host-gateway alias.

The official mutable `openspg-server:latest` tag is pulled for each candidate. The workflow resolves
and records the pulled digest in the protected runtime file so deployment and rollback use the exact
official artifact selected by that run. It never builds or patches an OpenSPG JAR or KAG wheel.
Each immutable release also contains the reviewed `schemas/` tree and its SHA-256 manifest under
`/opt/tidewise/reason-uat/releases/<release-id>/`. The atomic `state/current` link selects the
accepted Server configuration and Reason-owned content together.

## Infrastructure contract

Before Reason deploys, `tidewise-ai` must provide:

1. A healthy `tidewise-uat` Docker network with reachable `mysql` and `minio` aliases and valid
   MinIO credentials.
2. Host-native Neo4j reachable from `host-gateway:7687` with valid Reason credentials.
3. A Neo4j GDS release compatible with the installed Neo4j release; `RETURN gds.version()` must
   succeed in the `neo4j` database.
4. MySQL and the MinIO S3 API remain private. `tidewise-ai` independently owns the
   office-allowlisted Neo4j Browser/Bolt and MinIO Console ports; Reason only consumes their
   internal provider endpoints.
5. Its own middleware backup, upgrade, clearing and rollback procedures.

The Reason preflight checks this contract without modifying any middleware. A failed check stops the
Reason deployment before the Server is recreated.

## One-time ECS setup

Run as root after the `tidewise-deploy` user, Docker, Compose, the shared network and the existing
`/opt/tidewise/uat` shared lock directory are present:

```bash
sudo bash infra/uat/bootstrap-ecs.sh
```

Register a repository-scoped GitHub Actions Runner for `meierlink88/tidewise-reason` as the
`tidewise-deploy` user, with the labels `linux`, `x64` and `tidewise-uat-ecs`. Do not reuse a
repository-scoped runner registered to `tidewise-ai`.

## GitHub `uat` Environment

Create an Environment named `uat` with:

| Kind | Name | Purpose |
| --- | --- | --- |
| Variable | `UAT_RUNNER_NAME` | Exact name of the Reason repository Runner |
| Variable | `OPENSPG_NEO4J_USER` | Dedicated Neo4j user for Reason |
| Secret | `OPENSPG_MYSQL_ROOT_PASSWORD` | Password of the external OpenSPG MySQL database |
| Secret | `OPENSPG_JASYPT_PASSWORD` | UAT-only encryption password for Server-managed configuration |
| Secret | `OPENSPG_MINIO_ACCESS_KEY` | Access key of the external MinIO service |
| Secret | `OPENSPG_MINIO_SECRET_KEY` | Secret key of the external MinIO service |
| Secret | `OPENSPG_NEO4J_PASSWORD` | Password of the dedicated Neo4j user |

Passwords must contain 24-64 URL-safe characters (`A-Z`, `a-z`, `0-9`, `_`, `-`) because OpenSPG
receives the Neo4j credential in a connection URI. Never reuse the bundled local demo credentials.

## Deployment and verification

Dispatch **Deploy Reason UAT** from `main`. The selected commit must belong to `main` and have a
successful **CI** run. The workflow serializes with all existing UAT deployment workflows through
`/opt/tidewise/uat/deploy.lock`, pulls and resolves the official Server image, validates the external
dependencies (including authenticated, read-only MinIO and exact GDS `2.13.4` checks), publishes
the versioned Reason Schema artifacts, deploys only `server`, then verifies:

- container health and exact image ID;
- the Web and Actuator endpoints;
- import of the bundled `openspg-kag` distribution;
- `kag --help`, `knext --help`, and a real read-only `knext project list` call inside the official
  container.

After a successful deployment, run the office-network acceptance seam from outside the ECS:

```bash
curl --fail --show-error --silent http://123.60.99.198:8887/ >/dev/null
```

Huawei Cloud security-group source-IP rules are the outer UAT access boundary. This native HTTP
port is an explicitly accepted UAT exception and does not authorize unrestricted internet or
production exposure. Replace it with a managed HTTPS/VPN operator ingress when one is available.

Failure restores only the previous Reason Server release. It never invokes `docker compose down`,
uses `--remove-orphans`, or changes external middleware. The current reviewed
`schemas/Tidewise.schema` and its review fragments are deployed as versioned Reason-owned content,
but remain manual import candidates and are not automatically submitted by the deployment workflow.
