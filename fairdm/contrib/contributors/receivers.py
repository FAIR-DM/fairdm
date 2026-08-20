"""Signal receivers for the contributors app.

``Contribution.remove_user_perms`` (``models.py``) is a django-lifecycle
``AFTER_DELETE`` hook. django-lifecycle runs that hook from the model instance's own
``delete()`` method, which ``QuerySet.delete()`` bypasses entirely - a bulk delete never
calls each instance's ``delete()``, so the withdrawal never fired for a credit removed
that way (FR-036, design review RECON-002).

``withdraw_rights_on_credit_deletion`` below is a genuine Django ``post_delete`` signal
receiver instead. Django's deletion collector sends ``post_delete`` for every row it
collects regardless of whether the delete started from an instance or a queryset -
connecting a receiver here also disables the collector's "fast delete" fast path (which
skips sending signals when nothing listens for them), so the signal is guaranteed to
fire for both.
"""

from fairdm.utils.permissions import remove_all_model_perms


def withdraw_rights_on_credit_deletion(sender, instance, **kwargs):
    """Withdraw a person contributor's object-level rights over an object when their
    credit on it is deleted - including through a queryset delete (FR-036)."""
    from .models import Person

    if isinstance(instance.contributor, Person):
        remove_all_model_perms(instance.contributor, instance.content_object)
