# How to override a FairDM setting

FairDM gives a portal a complete set of Django settings. You override one when the value FairDM chose does not suit your portal, such as a longer email confirmation period or an extra password validator.

## Before you start

Your portal's settings module calls `fairdm.setup()`. [Settings](../reference/settings.md) lists every setting with its type and default.

## Steps

1. Find the setting in [Settings](../reference/settings.md). Note its type. Where the entry says the value comes from an environment variable, set the variable instead of assigning the setting, and skip to step 5.

2. Open the settings module that calls `fairdm.setup()`.

3. Assign the setting after the call, never inside it. `setup()` accepts no settings as arguments and raises `TypeError` if you pass one.

   ```python
   import fairdm

   fairdm.setup()

   ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 7
   ```

4. For a list or a dictionary, change the value in place so the entries FairDM put there stay.

   ```python
   # Add a validator of your own to the four FairDM sets
   AUTH_PASSWORD_VALIDATORS = AUTH_PASSWORD_VALIDATORS + [
       {"NAME": "my_portal.validators.ContainsDigitValidator"},
   ]

   # Change one entry of a dictionary
   REST_KNOX["TOKEN_LIMIT_PER_USER"] = 5

   # Add a logger
   LOGGING["loggers"]["my_app"] = {"handlers": ["console"], "level": "INFO"}
   ```

   Replace a whole list or dictionary only when the entry in [Settings](../reference/settings.md) says that is safe. `REST_FRAMEWORK`, `SPECTACULAR_SETTINGS` and `THUMBNAIL_ALIASES` hold entries FairDM's pages need.

5. Restart the portal and print the value Django uses.

   ```bash
   python manage.py shell -c "from django.conf import settings; print(settings.ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS)"
   ```

## The result

Django uses your value. An assignment after `fairdm.setup()` is the last layer, so it wins over FairDM's defaults, over an addon and over your portal's [environment override module](add-an-environment-override-module.md).

Some settings are built from others when `setup()` runs, so changing the source later does not change them. `CSRF_TRUSTED_ORIGINS` is built from `ALLOWED_HOSTS`, `CELERY_RESULT_BACKEND` from `CELERY_BROKER_URL` and `CELERY_TIMEZONE` from `DJANGO_TIME_ZONE`. The entry for each setting says which variable to set. To give a setting a different value in one environment only, use an [environment override module](add-an-environment-override-module.md) and not an `if` in the settings module.

`python manage.py show_config SETTING` does not see an assignment made after `setup()`. It reports the layer that set the value before your assignment. [Configuration](../reference/configuration.md#show_config) explains. For why assignment is the only route, see [How FairDM configures a portal](../../explanation/how-fairdm-configures-a-portal.md).
