"""FairDM allows you to lockdown your entire site with a password or restrict access to staff or superusers only. To enable this feature, you must set one of the following environment variables:

LOCKDOWN_PASSWORDS: A list of passwords that users can use to access the site.
LOCKDOWN_STAFF_ONLY: A boolean that restricts access to staff users only.
LOCKDOWN_SUPERUSERS_ONLY: A boolean that restricts access to superusers only.
LOCKDOWN_UNTIL_DATE: A date in ISO format (YYYY-MM-DD) until which the lockdown is active.
LOCKDOWN_AFTER_DATE: A date in ISO format (YYYY-MM-DD) after which the lockdown is active.
"""

from datetime import datetime

env = globals()["env"]

LOCKDOWN_ENABLED = any(
    [
        env("LOCKDOWN_STAFF_ONLY"),
        env("LOCKDOWN_SUPERUSERS_ONLY"),
        env("LOCKDOWN_PASSWORDS"),
        env("LOCKDOWN_UNTIL_DATE"),
        env("LOCKDOWN_AFTER_DATE"),
    ]
)

# if any(
#     [
#         env("LOCKDOWN_STAFF_ONLY"),
#         env("LOCKDOWN_SUPERUSERS_ONLY"),
#     ]
# ):
#     LOCKDOWN_FORM = "lockdown.forms.AuthForm"

LOCKDOWN_PASSWORDS = env("LOCKDOWN_PASSWORDS")

LOCKDOWN_AUTHFORM_STAFF_ONLY = env("LOCKDOWN_STAFF_ONLY")

LOCKDOWN_AUTHFORM_SUPERUSERS_ONLY = env("LOCKDOWN_SUPERUSERS_ONLY")

if env("LOCKDOWN_UNTIL_DATE"):
    try:
        LOCKDOWN_UNTIL_DATE = datetime.fromisoformat(env("LOCKDOWN_UNTIL_DATE"))
    except ValueError:
        raise ValueError(f"LOCKDOWN_UNTIL_DATE must be in ISO format (YYYY-MM-DD), got: {env('LOCKDOWN_UNTIL_DATE')}")

if env("LOCKDOWN_AFTER_DATE"):
    try:
        LOCKDOWN_AFTER_DATE = datetime.fromisoformat(env("LOCKDOWN_AFTER_DATE"))
    except ValueError:
        raise ValueError(f"LOCKDOWN_AFTER_DATE must be in ISO format (YYYY-MM-DD), got: {env('LOCKDOWN_AFTER_DATE')}")
