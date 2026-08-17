#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
official_image="spg-registry.cn-hangzhou.cr.aliyuncs.com/spg/openspg-server:latest"
configured_image="$(docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" config --images)"
test "$configured_image" = "$official_image"

official_image_id="$(docker image inspect "$official_image" --format '{{.Id}}')"
running_image_id="$(docker inspect reason-server --format '{{.Image}}')"
test "$running_image_id" = "$official_image_id"

docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" exec -T server \
  python -c "import importlib.metadata; print(importlib.metadata.version('openspg-kag'))" >/dev/null
docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" exec -T \
  -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 server kag --help >/dev/null
docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" exec -T \
  -e KAG_PROJECT_HOST_ADDR=http://127.0.0.1:8887 server knext --help >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8887/actuator/health >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8887/ >/dev/null

image_digest="$(docker image inspect "$official_image" --format '{{join .RepoDigests ","}}')"
kag_version="$(docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" exec -T server \
  python -c "import importlib.metadata; print(importlib.metadata.version('openspg-kag'))")"
printf 'Verified official OpenSPG image %s (%s), bundled KAG %s\n' \
  "$official_image" "$image_digest" "$kag_version"
