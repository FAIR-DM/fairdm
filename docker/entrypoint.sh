#!/bin/sh
# Start sequence of the FairDM base images.
#
#   web (default)  migrate, collect static files, run the start steps, then serve with gunicorn
#   worker [args]  run a Celery worker; extra arguments go to Celery
#   anything else  run as given
#
# Start steps are the executable files in FAIRDM_START_DIR (default /docker-entrypoint.d), run in
# name order after collectstatic. A file that is not executable is skipped with a line on stderr.
# Any failing step stops the start with its exit status.
set -eu

start_dir="${FAIRDM_START_DIR:-/docker-entrypoint.d}"

case "${1:-web}" in
  web)
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    for step in "$start_dir"/*; do
      [ -f "$step" ] || continue
      if [ -x "$step" ]; then
        "$step"
      else
        echo "skipping $step: not executable" >&2
      fi
    done
    exec gunicorn "${WSGI_APP:-config.wsgi:application}"
    ;;
  worker)
    shift
    exec celery --app "${CELERY_APP:-config}" worker "$@"
    ;;
  *)
    exec "$@"
    ;;
esac
