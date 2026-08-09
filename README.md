# Agent OS: OpenSPG + KAG

Local OpenSPG 0.8 and KAG 0.8 evaluation environment. Docker Compose uses the project/group name
`agent-os`.

## Start

```bash
./scripts/install-kag.sh
./scripts/start.sh
```

Open <http://127.0.0.1:8887> and sign in with the official local demo account:

- Username: `openspg`
- Password: `openspg@kag`

The KAG developer commands are available at `.venv/bin/kag` and `.venv/bin/knext`.

## Tidewise Schema

The OpenSPG project `Tidewise` currently uses its pre-projection default Schema. The combined
Tidewise TBox projection in [`schemas/Tidewise.schema`](schemas/Tidewise.schema) is an unapproved,
inactive draft; review each type before any future submission. No PostgreSQL ABox facts have been
imported.

## Services

| Service | Local address |
| --- | --- |
| OpenSPG/KAG Web | <http://127.0.0.1:8887> |
| Neo4j Browser | <http://127.0.0.1:7474> |
| MinIO Console | <http://127.0.0.1:9001> |
| MySQL | `127.0.0.1:3306` |

## Stop

```bash
./scripts/stop.sh
```

Persistent Docker volumes are retained. To remove this installation's data as well, run
`docker compose down --volumes` explicitly.

The base UI can run without a model provider. Building a knowledge base and using KAG inference
requires configuring a generation model and an embedding model in the product UI.

See [the local deployment design](docs/design/local-openspg-kag.md) for boundaries and recovery.
