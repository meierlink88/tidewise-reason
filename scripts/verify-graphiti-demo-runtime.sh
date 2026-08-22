#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

bash "$repo_root/infra/graphiti/verify.sh"
bash "$repo_root/scripts/graphiti-demo.sh" evidence-smoke
bash "$repo_root/scripts/graphiti-demo.sh" verify
