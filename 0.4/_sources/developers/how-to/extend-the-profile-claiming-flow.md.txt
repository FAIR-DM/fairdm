# How to extend the profile-claiming flow

A profile is claimed when its owner signs in with ORCID or confirms the email address the profile holds. This guide adds logic of your own to those routes and records a claim that your own code makes. Use it when your portal needs to do something extra when a profile is taken over, such as notifying a team or setting up a default.

## Steps

1. To change what happens when someone signs in with ORCID, subclass `SocialAccountAdapter` and override `pre_social_login`. When FairDM finds an unclaimed profile that holds the signing-in ORCID iD, `super().pre_social_login` claims it and raises allauth's `ImmediateHttpResponse`. Catch it to run logic after a claim, and raise it again.

   ```python
   # myportal/adapters.py
   from allauth.core.exceptions import ImmediateHttpResponse

   from fairdm.contrib.contributors.adapters import SocialAccountAdapter


   class PortalSocialAccountAdapter(SocialAccountAdapter):
       def pre_social_login(self, request, sociallogin):
           # Code here runs for every ORCID sign-in, before FairDM looks for a profile.
           try:
               super().pre_social_login(request, sociallogin)
           except ImmediateHttpResponse:
               if sociallogin.user.is_claimed:
                   ...  # your logic for a profile that was just claimed
               raise
   ```

2. Name your adapter in `SOCIALACCOUNT_ADAPTER`.

   ```python
   # settings.py
   SOCIALACCOUNT_ADAPTER = "myportal.adapters.PortalSocialAccountAdapter"
   ```

   To set the setting without replacing FairDM's other values, see [How to override a FairDM setting](override-a-fairdm-setting.md).

3. To run logic after a claim by any route, connect a `post_save` receiver for `Person`. Every claiming service saves the person with `update_fields` that include `is_claimed`, and so does a merge.

   ```python
   # myportal/receivers.py
   from django.db.models.signals import post_save
   from django.dispatch import receiver

   from fairdm.contrib.contributors.models import Person


   @receiver(post_save, sender=Person)
   def after_claim(sender, instance, created, update_fields, **kwargs):
       if update_fields and "is_claimed" in update_fields and instance.is_claimed:
           ...  # your logic
   ```

   Import the module when your app is ready, so the receiver is connected.

   ```python
   # myportal/apps.py
   from django.apps import AppConfig


   class PortalConfig(AppConfig):
       name = "myportal"

       def ready(self):
           from . import receivers  # noqa: F401
   ```

4. To claim a profile from your own code, call the service for the route and handle `ClaimingError`. Its message is safe to show to the user.

   ```python
   from fairdm.contrib.contributors.exceptions import ClaimingError
   from fairdm.contrib.contributors.services.claiming import claim_via_orcid

   try:
       claimed = claim_via_orcid(person, sociallogin)
   except ClaimingError as error:
       messages.error(request, str(error))
   ```

   `claim_via_email(person)` does nothing and returns `None` unless `ACCOUNT_EMAIL_VERIFICATION` is `"mandatory"`.

5. To record a claim that no service wrote, add an entry to the audit log with `log_claiming_event`. FairDM writes no entry with the method `ClaimMethod.ADMIN_MANUAL`, so use it for an activation of your own.

   ```python
   from fairdm.contrib.contributors.models import ClaimMethod
   from fairdm.contrib.contributors.utils.audit import log_claiming_event

   log_claiming_event(
       method=ClaimMethod.ADMIN_MANUAL,
       source=unclaimed_person,
       target=activated_person,
       initiated_by=request.user,
       ip_address=request.META.get("REMOTE_ADDR"),
       success=True,
       details={"note": "Activated by hand."},
   )
   ```

## The result

Your adapter and receiver run alongside the shipped claiming code, and a claim of your own appears in the claiming audit log, which administrators read in [Claiming audit logs](../../administrators/reference/claiming-audit-log.md). The functions, exceptions and models are listed in [Profile claiming](../reference/profile-claiming.md). The routes and the reasons for them are in [How a profile is claimed](../../explanation/how-a-profile-is-claimed.md).
