#!/usr/bin/env bash

set -euo pipefail

prototype_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output="$($prototype_root/run.sh)"

printf '%s\n' "$output"

grep -F 'PASS runtime=local-reason-server' <<<"$output" >/dev/null
grep -F 'PASS model=DeepSeek V4 Flash' <<<"$output" >/dev/null
grep -F 'PASS graph=3-nodes-2-edges' <<<"$output" >/dev/null
grep -F 'PASS positive-answer=铜' <<<"$output" >/dev/null
grep -F 'PASS positive-path=示例电缆公司->电力电缆->铜' <<<"$output" >/dev/null
grep -F 'PASS negative-answer=no-evidence' <<<"$output" >/dev/null
