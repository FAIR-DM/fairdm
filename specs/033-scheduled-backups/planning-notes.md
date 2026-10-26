# Planning notes: scheduled, encrypted backups of the database and media

Suggestions from the maintainer for research and planning. The plan answers each one by name.

## Ship the schedules as django-celery-beat entries

"We already include celery_beat which I'm pretty sure allows portal devs to set task schedules in
the admin site. We should be shipping items in celery_beat by default, then a dev can change it in
the admin site if required."

## Encrypt by default

"I think backups should be encrypted by default."
