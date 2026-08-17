#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$repo_root/upstreams.lock"
image_name="${TIDEWISE_REASON_IMAGE:-tidewise-reason:openspg-0.8-kag-0.8.0}"
kag_source="$repo_root/.runtime/upstream/kag"

hash_file() {
  if command -v sha256sum >/dev/null; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

label_value() {
  docker image inspect "$image_name" --format "{{ index .Config.Labels \"$1\" }}"
}

test "$(label_value io.tidewise.openspg.commit)" = "$OPENSPG_COMMIT"
test "$(label_value io.tidewise.kag.commit)" = "$KAG_COMMIT"
test "$(label_value io.tidewise.openspg.version)" = "$OPENSPG_VERSION"
test "$(label_value io.tidewise.kag.version)" = "$KAG_VERSION"
test "$(label_value io.tidewise.openspg.jar.sha256)" = \
  "$(hash_file "$repo_root/.runtime/build/openspg/arks-sofaboot-0.8-executable.jar")"
kag_wheel="$(find "$repo_root/.runtime/build/kag" -maxdepth 1 -type f -name '*.whl')"
test "$(label_value io.tidewise.kag.wheel.sha256)" = "$(hash_file "$kag_wheel")"

for relative_file in knext/schema/marklang/schema_ml.py knext/schema/model/base.py; do
  local_hash="$(hash_file "$kag_source/$relative_file")"
  image_hash="$(docker run --rm --entrypoint python "$image_name" -c \
    "import hashlib, pathlib; p=pathlib.Path('/opt/tidewise/venv/lib/python3.10/site-packages/$relative_file'); print(hashlib.sha256(p.read_bytes()).hexdigest())")"
  test "$local_hash" = "$image_hash"

  if [[ -x "$repo_root/.venv/bin/python" ]]; then
    module_name="${relative_file%.py}"
    module_name="${module_name//\//.}"
    local_runtime_hash="$("$repo_root/.venv/bin/python" -c \
      "import hashlib, importlib.util, pathlib; p=pathlib.Path(importlib.util.find_spec('$module_name').origin); print(hashlib.sha256(p.read_bytes()).hexdigest())")"
    test "$local_hash" = "$local_runtime_hash"
  fi
done

docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" exec -T server \
  python -c "import importlib.metadata; assert importlib.metadata.version('openspg-kag') == '0.8.0'"
docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" exec -T server kag --help >/dev/null
docker compose --project-directory "$repo_root" -f "$repo_root/compose.yaml" exec -T server knext --help >/dev/null
curl --fail --silent --show-error http://127.0.0.1:8887/actuator/health >/dev/null
"$repo_root/scripts/check-kag-thinker-pipeline.sh"

printf 'Verified OpenSPG %s (%s) with KAG %s (%s)\n' \
  "$OPENSPG_VERSION" "$OPENSPG_COMMIT" "$KAG_VERSION" "$KAG_COMMIT"
