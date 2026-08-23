"""Signal receivers for the contributors app.

Withdrawing a person's rights over an object when their credit on it is removed used to
be a django-lifecycle ``AFTER_DELETE`` hook on ``Contribution``. django-lifecycle runs
that hook from the model instance's own ``delete()``, which ``QuerySet.delete()``
bypasses entirely - a bulk delete never calls each instance's ``delete()``, so the
withdrawal never fired for a credit removed that way (FR-036, design review RECON-002).

``withdraw_rights_on_credit_deletion`` below is a genuine Django ``post_delete`` signal
receiver instead. Django's deletion collector sends ``post_delete`` for every row it
collects regardless of whether the delete started from an instance or a queryset -
connecting a receiver here also disables the collector's "fast delete" fast path (which
skips sending signals when nothing listens for them), so the signal is guaranteed to
fire for both. It covers every path the hook did, so the hook has been removed rather
than left to run a second time alongside it.
"""

from fairdm.utils.permissions import remove_all_model_perms


def withdraw_rights_on_credit_deletion(sender, instance, **kwargs):
    """Withdraw a person contributor's object-level rights over an object when their
    credit on it is deleted - including through a queryset delete (FR-036).

    ``content_object`` is ``None`` when the credited object is what is being deleted and
    the credit is following it down the cascade: the collector removes the project or
    dataset row first, so the generic reference no longer resolves by the time this
    fires. There is no object left to hold a right over, so there is nothing to
    withdraw. Rights recorded against the deleted object are cleared by
    ``clean_orphan_obj_perms``, which is where they belong - every object deletion
    leaves them behind, credited or not.
    """
    from .models import Person

    if instance.content_object is None:
        return

    if isinstance(instance.contributor, Person):
        remove_all_model_perms(instance.contributor, instance.content_object)
