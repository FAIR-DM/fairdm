import logging

from allauth.account.signals import user_signed_up
from django.contrib.auth import get_user_model
from django.dispatch import receiver

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(user_signed_up)
def create_profile(request, user, **kwargs):
    """Find a matching contributor profile or create a new one"""

    # if the user signed up with orcid, it will be available on the user object
    # we can use it to see if a profile is already associated with the user

    if orcid := user.get_provider("orcid"):
        # copies the extra data from the orcid provider to the user object
        user.synced_data = orcid.extra_data
        user.save()


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         profile, created = Contributor.objects.get_or_create(user=instance, defaults={"name": instance.get_full_name()})
#         print(profile, created)
#         if created:
#             logger.info(f"Created new profile for {instance.username}")
