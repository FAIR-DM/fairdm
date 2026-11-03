# How to configure the agreement check

The agreement check sends a signed-in person who has not agreed to a required legal document to the page that asks. You configure it when your portal needs other pages to stay reachable, when some accounts should never be held up, or when you want a different place to land after agreeing.

## Before you start

You need to edit the portal's settings module and restart the portal. Every setting here belongs to django-mvp-compliance and is described in [Settings](../reference/settings.md). Who the check holds up is explained in [Who is asked to agree to a legal document](../../explanation/who-is-asked-to-agree-to-a-legal-document.md).

## Steps

1. Open the settings module that calls `fairdm.setup()`, and make the changes after that call.

2. To keep more of your own pages reachable for a person who has not agreed, add to `MVP_COMPLIANCE_AGREEMENT_EXEMPT_URLS`. FairDM sets it to `["/hijack/"]`, so add to the list rather than replacing it.

   ```python
   MVP_COMPLIANCE_AGREEMENT_EXEMPT_URLS += ["/help/", "/contact/"]
   ```

   An entry covers its address and everything beneath it, compared one path segment at a time. The setting is a list even for one entry.

3. To let named accounts through without asking, list their usernames in `MVP_COMPLIANCE_AGREEMENT_EXEMPT_USERS`.

   ```python
   MVP_COMPLIANCE_AGREEMENT_EXEMPT_USERS = ["service-account"]
   ```

4. To record the address a person agreed from, turn on `MVP_COMPLIANCE_RECORD_IP_ADDRESS`. It is off by default, because an address is personal data.

   ```python
   MVP_COMPLIANCE_RECORD_IP_ADDRESS = True
   ```

5. To send a person somewhere other than the home page after they agree, when they were not on their way to another page, set `MVP_COMPLIANCE_AGREEMENT_REDIRECT_URL`.

   ```python
   MVP_COMPLIANCE_AGREEMENT_REDIRECT_URL = "/welcome/"
   ```

6. To change how long a clear finding is remembered in the person's session, set `MVP_COMPLIANCE_AGREEMENT_CHECK_INTERVAL` to a number of seconds. The default is 60, and `0` checks every request.

   ```python
   MVP_COMPLIANCE_AGREEMENT_CHECK_INTERVAL = 300
   ```

7. To stop asking altogether, take the check out of `MIDDLEWARE`. The document pages and the records of who agreed stay.

   ```python
   MIDDLEWARE.remove("mvp_compliance.middleware.AgreementMiddleware")
   ```

8. Restart the portal.

## The result

The check follows the new settings from the next request. Run `python manage.py check` to confirm the configuration. A list setting given as a string, or an interval that is not a number, is reported with an ID from `mvp_compliance.E001` to `mvp_compliance.E004`, which are listed in [Legal documents](../reference/legal-documents.md).

An account that holds the `mvp_compliance.skip_agreement` permission is also let through. Give the permission to a group in the administration interface instead of listing usernames when the exemption belongs to a role.
