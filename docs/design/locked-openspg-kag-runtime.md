# Locked OpenSPG and KAG runtime

Tidewise Reason is an extension project. It does not fork OpenSPG or KAG. It owns the
version contract, compatibility overrides, ontology inputs, fact inputs, and reasoning
experiments built on top of those two upstream projects.

## Source contract

The authoritative revisions are recorded in `upstreams.lock`:

- OpenSPG `v0.8` at `ceeb3ef549df79ca4c4878e7ff452c73584991f3`.
- KAG `v0.8.0` at `de777280584fec0c3d888804eaafa86f169f13db`.

`scripts/sync-upstreams.sh` restores detached, clean checkouts below
`.runtime/upstream/`. Those checkouts are deliberately ignored by Git. The script rejects a
modified checkout rather than silently discarding local work.

The KAG dependency lock is compiled from the locked checkout's `requirements.txt` plus
`pemja==0.4.0`, which OpenSPG needs for embedded Python operators.

OpenSPG builds with `config/maven-settings.xml` and an isolated repository under `.runtime/`.
This deliberately ignores a developer's personal Maven mirrors and fails on checksum errors;
only Maven Central and the OSGeo release repository are allowed.

## Build and local CLI

Run:

```bash
./scripts/build-runtime.sh
./scripts/install-kag.sh
```

The first command builds the OpenSPG executable JAR and the KAG wheel from the restored source,
then assembles `tidewise-reason:openspg-0.8-kag-0.8.0`. The second command installs the same
KAG checkout into the repository-local `.venv` for `kag` and `knext` commands.

The image records both upstream versions and commits as OCI labels. It contains no Tidewise
schema or fact data.

## Deployment and verification

The Compose service keeps the established project, service, container, network, and port names.
It replaces only the `reason-server` container and continues to use shared middleware managed
outside this repository.

```bash
./scripts/stop.sh
./scripts/start.sh
./scripts/verify-runtime.sh
```

Verification checks the OCI labels, KAG parser source hashes in the checkout/image/local
environment, both CLIs, the Web endpoint, and the official KAG 0.8.0 thinker planner contract.

Old `.runtime/KAG` and the previous `.venv` may be removed only after the replacement image
has built successfully. Shared MySQL, Neo4j, and MinIO containers or volumes must not be removed
by this repository.
