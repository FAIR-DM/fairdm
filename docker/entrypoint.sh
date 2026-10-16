#!/bin/sh
# Start sequence of the FairDM base images.
#
#   web (default)  migrate, collect and compress static files, then serve with gunicorn
#   worker [args]  run a Celery worker; extra arguments go to Celery
#   anything else  run as given
#
# Any failing step stops the start with its exit status.
set -eu

case "${1:-web}" in
  web)
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput
    python manage.py compress
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
