"""Celery settings: the shared Redis broker and result backend at ``REDIS_URL``.

Owns the background-task settings. A portal supplies task-specific time limits and the beat
schedule. It may also run no worker at all.
"""

env = globals()["env"]

CELERY_TIMEZONE = env("DJANGO_TIME_ZONE")

CELERY_RESULT_EXTENDED = True

# https://github.com/celery/celery/pull/6122
CELERY_RESULT_BACKEND_ALWAYS_RETRY = True

CELERY_RESULT_BACKEND_MAX_RETRIES = 10

CELERY_ACCEPT_CONTENT = ["json"]

CELERY_TASK_SERIALIZER = "json"

CELERY_RESULT_SERIALIZER = "json"

CELERY_TASK_TIME_LIMIT = 5 * 60

CELERY_TASK_SOFT_TIME_LIMIT = 60

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_WORKER_SEND_TASK_EVENTS = True

CELERY_TASK_SEND_SENT_EVENT = True

CELERY_TASK_EAGER_PROPAGATES = True

CELERY_BROKER_URL = env("REDIS_URL")

CELERY_RESULT_BACKEND = CELERY_BROKER_URL

CELERY_TASK_ALWAYS_EAGER = False
