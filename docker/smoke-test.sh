#!/usr/bin/env bash
# Checks what only built images can show: what the base images contain, and that a portal built
# on them with docker/portal.Dockerfile starts from an empty database and serves requests.
#
#   docker/smoke-test.sh RUNTIME_IMAGE DEVELOPMENT_IMAGE PORTAL_IMAGE
#
# Needs a PostGIS database that is empty and a Redis server. Where they are comes from these
# environment variables, whose defaults suit a CI runner with service containers on localhost:
#
#   SMOKE_NETWORK      Docker network the portal containers join (default: host)
#   SMOKE_DB_HOST      PostGIS host as the containers see it (default: localhost)
#   SMOKE_REDIS_URL    Redis URL as the containers see it (default: redis://localhost:6379/0)
#   POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#                      database settings (defaults: 5432, fairdm, postgres, postgres)
#   DOCKER             the docker command (default: docker)
#
# Docker Desktop does not give containers the host's network, so locally start the services on a
# network of their own and join it:
#
#   docker network create fairdm-smoke
#   docker run -d --name fairdm-smoke-db --network fairdm-smoke -e POSTGRES_PASSWORD=postgres \
#       -e POSTGRES_DB=fairdm postgis/postgis:17-3.5
#   docker run -d --name fairdm-smoke-redis --network fairdm-smoke redis:7
#   SMOKE_NETWORK=fairdm-smoke SMOKE_DB_HOST=fairdm-smoke-db \
#       SMOKE_REDIS_URL=redis://fairdm-smoke-redis:6379/0 \
#       DOCKER=docker.exe docker/smoke-test.sh fairdm-base:local fairdm-base:local-dev fairdm-demo:local
#
# Each check prints one line. The script stops at the first failure.

set -euo pipefail

if [ "$#" -ne 3 ]; then
    echo "usage: $0 RUNTIME_IMAGE DEVELOPMENT_IMAGE PORTAL_IMAGE" >&2
    exit 2
fi
runtime_image=$1
development_image=$2
portal_image=$3

docker=${DOCKER:-docker}
network=${SMOKE_NETWORK:-host}
db_host=${SMOKE_DB_HOST:-localhost}
redis_url=${SMOKE_REDIS_URL:-redis://localhost:6379/0}
db_port=${POSTGRES_PORT:-5432}
db_name=${POSTGRES_DB:-fairdm}
db_user=${POSTGRES_USER:-postgres}
db_password=${POSTGRES_PASSWORD:-postgres}

run_id=$$
containers=()
step_dir=$(mktemp -d)

cleanup() {
    rm -rf "$step_dir"
    if [ "${#containers[@]}" -gt 0 ]; then
        "$docker" rm --force "${containers[@]}" >/dev/null 2>&1 || true
    fi
}
trap cleanup EXIT

pass() { echo "ok   $1"; }

fail() {
    echo "FAIL $1" >&2
    if [ -n "${2:-}" ]; then
        echo "---- last log lines of $2" >&2
        "$docker" logs --tail 40 "$2" >&2 2>&1 || true
    fi
    exit 1
}

# Everything a portal container reads from its environment. The guide lists the same variables.
portal_env() {
    local secret_key
    secret_key=$(head -c 48 /dev/urandom | od -An -tx1 | tr -d ' \n')
    printf '%s\n' \
        "DJANGO_SECRET_KEY=$secret_key" \
        "DJANGO_SITE_DOMAIN=localhost" \
        "POSTGRES_HOST=${POSTGRES_HOST_OVERRIDE:-$db_host}" \
        "POSTGRES_PORT=$db_port" \
        "POSTGRES_DB=$db_name" \
        "POSTGRES_USER=$db_user" \
        "POSTGRES_PASSWORD=$db_password" \
        "REDIS_URL=$redis_url"
}

# start_portal NAME [-e VAR=value ...] [-- COMMAND...]: start a detached portal container and
# leave its name in $started. Not called in a subshell, so cleanup knows the container. When
# $copy_into_start_dir is set, the files in that directory are copied into /docker-entrypoint.d
# before the container starts. They are copied, not bind-mounted, because Docker Desktop cannot
# mount a path from the WSL filesystem.
start_portal() {
    local name="smoke-$1-$run_id" args=() env_args=() line
    shift
    while [ "$#" -gt 0 ] && [ "$1" != "--" ]; do
        args+=("$1")
        shift
    done
    [ "${1:-}" = "--" ] && shift
    while IFS= read -r line; do
        env_args+=(-e "$line")
    done < <(portal_env)
    containers+=("$name")
    "$docker" create --name "$name" --network "$network" "${env_args[@]}" "${args[@]}" \
        "$portal_image" "$@" >/dev/null
    if [ -n "${copy_into_start_dir:-}" ]; then
        "$docker" cp "$copy_into_start_dir/." "$name:/docker-entrypoint.d" >/dev/null
    fi
    "$docker" start "$name" >/dev/null
    started=$name
}

# status CONTAINER PORT: the HTTP status of / as a proxy in front of the portal would see it.
# Asked from inside the container, so it works the same on every network.
status() {
    "$docker" exec "$1" python -c "
import sys, urllib.request
request = urllib.request.Request(
    'http://localhost:$2/', headers={'X-Forwarded-Proto': 'https'}
)
try:
    print(urllib.request.urlopen(request, timeout=10).status)
except Exception as error:
    print(getattr(error, 'code', 0))
" 2>/dev/null || echo 0
}

# wait_for_200 CONTAINER PORT: wait until / answers 200, failing early if the container exits.
wait_for_200() {
    local name=$1 port=$2 waited=0
    while [ "$waited" -lt 240 ]; do
        if [ "$("$docker" inspect --format '{{.State.Running}}' "$name")" != "true" ]; then
            fail "$name exited before answering on port $port" "$name"
        fi
        if [ "$(status "$name" "$port")" = "200" ]; then
            return 0
        fi
        sleep 2
        waited=$((waited + 2))
    done
    fail "$name did not answer 200 on port $port within 240 seconds" "$name"
}

# --- What the images contain ---------------------------------------------------------------

in_image() { "$docker" run --rm --entrypoint sh "$1" -c "$2"; }

in_image "$runtime_image" 'ldconfig -p | grep -q "libpq.so.5"' \
    || fail "the runtime image has no libpq.so.5"
pass "the runtime image has the PostgreSQL client library"

in_image "$runtime_image" 'uv --version >/dev/null' || fail "the runtime image has no uv"
pass "the runtime image has uv"

for image in "$runtime_image" "$development_image"; do
    if in_image "$image" 'python -c "import fairdm"' >/dev/null 2>&1; then
        fail "$image contains FairDM"
    fi
    pass "$image does not contain FairDM"
done

in_image "$development_image" 'command -v gcc >/dev/null' || fail "the development image has no gcc"
in_image "$development_image" 'command -v git >/dev/null' || fail "the development image has no git"
pass "the development image has gcc and git"

# --- A portal built on the images ----------------------------------------------------------

db_probe="import socket; socket.create_connection(('$db_host', $db_port), timeout=3)"
waited=0
until "$docker" run --rm --network "$network" --entrypoint python "$runtime_image" \
    -c "$db_probe" >/dev/null 2>&1; do
    waited=$((waited + 2))
    [ "$waited" -lt 60 ] || fail "the database at $db_host:$db_port is not reachable"
    sleep 2
done
pass "the database is reachable from a container on network $network"

# A start step a portal would add: it fails unless the migrations have already run.
cat >"$step_dir/10-check-migrations" <<'STEP'
#!/bin/sh
set -eu
python manage.py shell -c "
from django.db import connection
assert 'django_migrations' in connection.introspection.table_names()
"
echo "start step: django_migrations exists" >&2
STEP
chmod 755 "$step_dir/10-check-migrations"

copy_into_start_dir=$step_dir start_portal web
web=$started
wait_for_200 "$web" 8000
pass "the portal migrated, collected static files and answered 200 on port 8000"

web_log=$("$docker" logs "$web" 2>&1)
step_line=$(printf '%s\n' "$web_log" | grep -n "start step: django_migrations exists" | head -1 | cut -d: -f1 || true)
server_line=$(printf '%s\n' "$web_log" | grep -n "Listening at" | head -1 | cut -d: -f1 || true)
[ -n "$step_line" ] || fail "the start step did not run" "$web"
[ -n "$server_line" ] || fail "no 'Listening at' line from the server" "$web"
[ "$step_line" -lt "$server_line" ] || fail "the start step ran after the server started" "$web"
pass "a start step in /docker-entrypoint.d saw the migrated database and ran before the server answered"

uids=$("$docker" exec "$web" sh -c '
    for dir in /proc/[0-9]*; do
        if tr "\0" " " < "$dir/cmdline" 2>/dev/null | grep -q gunicorn; then
            awk "/^Uid:/ {print \$2}" "$dir/status"
        fi
    done')
[ -n "$uids" ] || fail "no gunicorn process found in $web" "$web"
for uid in $uids; do
    [ "$uid" != "0" ] || fail "the server runs as root" "$web"
done
pass "the server does not run as root"

"$docker" exec "$web" sh -c '
    test -z "${GDAL_LIBRARY_PATH:-}" && test -z "${GEOS_LIBRARY_PATH:-}" &&
    python -c "from django.contrib.gis import gdal, geos; gdal.gdal_version(); geos.geos_version()"' \
    >/dev/null 2>&1 || fail "GDAL and GEOS did not load with no library path set" "$web"
pass "GDAL and GEOS load with no library path set"

start_portal port -e PORT=8123
other_port=$started
wait_for_200 "$other_port" 8123
pass "PORT=8123 makes the portal answer on port 8123"

start_portal worker -- worker --loglevel INFO --concurrency 1
worker=$started
waited=0
until "$docker" logs "$worker" 2>&1 | grep -q " ready\."; do
    [ "$("$docker" inspect --format '{{.State.Running}}' "$worker")" = "true" ] \
        || fail "the worker exited" "$worker"
    waited=$((waited + 2))
    [ "$waited" -lt 120 ] || fail "the worker was not ready within 120 seconds" "$worker"
    sleep 2
done
if "$docker" logs "$worker" 2>&1 | grep -qE "Running migrations|Operations to perform|static files"; then
    fail "the worker ran the web start sequence" "$worker"
fi
pass "the worker command started Celery and ran none of the web start sequence"

POSTGRES_HOST_OVERRIDE=unreachable.invalid
start_portal unreachable
unreachable=$started
exit_code=$(timeout 120 "$docker" wait "$unreachable") \
    || fail "a container with an unreachable database was still running after 120 seconds" "$unreachable"
[ "$exit_code" != "0" ] || fail "a container with an unreachable database exited 0" "$unreachable"
if "$docker" logs "$unreachable" 2>&1 | grep -q "Listening at"; then
    fail "the server started with an unreachable database" "$unreachable"
fi
pass "with the database unreachable the container exits $exit_code and the server never starts"

echo "all checks passed"
