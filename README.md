# Tidewise Reason: OpenSPG + KAG

Local OpenSPG and KAG evaluation environment. The official OpenSPG Server `latest` image is the
sole runtime release. Reason Server joins the shared `tidewise-app` project and consumes MySQL,
Neo4j and MinIO from `tidewise-infra`.

## Start

```bash
./scripts/start.sh
```

Open <http://127.0.0.1:8887> and sign in with the official local demo account:

- Username: `openspg`
- Password: `openspg@kag`

`start.sh` pulls the official image before recreating only the `server` service. The bundled KAG
developer commands are available inside the container:

```bash
docker compose exec -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 server kag --help
docker compose exec -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 server knext --help
```

This repository does not build OpenSPG or KAG from source and does not inject a replacement JAR or
wheel into the official image.

## Tidewise Schema

The OpenSPG project `Tidewise` currently uses its pre-projection default Schema. The manual-review
import candidate in [`schemas/Tidewise.schema`](schemas/Tidewise.schema) preserves those KAG
foundation types and represents all 16 active PostgreSQL TBox entity types. It has not been
submitted to OpenSPG, and no PostgreSQL ABox facts have been imported.

## Services

This repository starts only the `reason-server` OpenSPG/KAG Web container. The remaining endpoints
belong to the independently operated shared infrastructure stack.

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

The stop script removes only Reason Server. It never stops shared infrastructure or removes its
persistent volumes. Do not run unscoped `docker compose down` or `--remove-orphans` in this
repository.

The base UI can run without a model provider. Building a knowledge base and using KAG inference
requires configuring a generation model and an embedding model in the product UI.

See [the local deployment design](docs/design/local-openspg-kag.md) and
[the official runtime policy](docs/design/official-openspg-kag-runtime.md) for boundaries,
extension seams and recovery.
