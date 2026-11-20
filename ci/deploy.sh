#!/usr/bin/env bash
set -euo pipefail

registry="${1:?provide the image repository}"
candidate_ref="${2:?provide the full commit SHA}"
candidate="$registry:$candidate_ref"
pointer="$registry:approved"
python="${PYTHON_COMMAND:-python}"
local_port="${LOCAL_PORT:-8196}"
audit=evidence/deploy
mkdir -p "$audit"

verify_slot() {
    local image="$1" revision="$2" phase="$3" cid status=0
    export GATEWAY_IMAGE="$image"
    printf '\n=== %s %s ===\n' "$phase" "$revision"
    docker compose up -d --force-recreate --pull never --wait --wait-timeout 22 \
        2>&1 | tee "$audit/$phase-compose.log" || status=1
    cid=$(docker compose ps --all --quiet gateway) || status=1
    if [[ -n "$cid" ]]; then
        "$python" -m pytest -q runtime --hosts="docker://$cid" \
            --junitxml="$audit/$phase-runtime.xml" 2>&1 | tee "$audit/$phase-runtime.log" || status=1
    else
        printf 'Gateway container did not start\n' | tee "$audit/$phase-runtime.log"
        status=1
    fi
    "$python" ci/http_check.py "$local_port" "$revision" | tee "$audit/$phase-http.log" || status=1
    docker compose logs --no-color --timestamps gateway > "$audit/$phase-container.log" 2>&1 || status=1
    return "$status"
}

previous=""
previous_ref=""
if docker pull "$pointer" > "$audit/approved-pull.log" 2>&1; then
    digest=$(sed -n 's/^Digest: //p' "$audit/approved-pull.log")
    [[ "$digest" =~ ^sha256:[0-9a-f]{64}$ ]]
    previous="$registry@$digest"
    previous_ref=$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "$previous")
    [[ "$previous_ref" =~ ^[0-9a-f]{40}$ ]]
    verify_slot "$previous" "$previous_ref" baseline
elif ! grep -Eiq 'manifest unknown|not found' "$audit/approved-pull.log"; then
    cat "$audit/approved-pull.log" >&2
    exit 1
fi

if verify_slot "$candidate" "$candidate_ref" incoming &&
   docker tag "$candidate" "$pointer" &&
   docker push "$pointer" 2>&1 | tee "$audit/promote.log"; then
    printf 'Approved revision: %s\n' "$candidate_ref"
    exit 0
fi

printf 'Rejected revision: %s\n' "$candidate_ref"
if [[ -n "$previous" ]]; then
    printf 'Recovering verified digest %s\n' "$digest"
    if verify_slot "$previous" "$previous_ref" recovered; then
        printf 'Rollback verified: HTTP 200, commit %s\n' "$previous_ref"
    else
        printf 'Rollback validation failed\n' >&2
    fi
fi
exit 1
