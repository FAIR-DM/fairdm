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

``refuse_off_vocabulary_role`` enforces FR-032 for the same structural reason:
``Contribution.clean()`` documents the rule, but Django's ``full_clean()`` never
validates many-to-many data, ``self.roles`` on a saved instance reads what is already
stored rather than what a caller is about to write, and no production write path calls
``full_clean()`` before writing anyway. Every write reaches ``Contribution.roles``
through ``roles.add()`` or ``roles.set()`` (``set()`` decomposes into ``remove()`` +
``add()`` internally - see Django's ``ManyRelatedManager.set()``), so an ``m2m_changed``
receiver on ``pre_add`` is the one place that sees every write before it commits.
"""

from django.core.exceptions import ValidationError

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


def refuse_off_vocabulary_role(sender, action, reverse, model, pk_set, **kwargs):
    """Refuse a role drawn from any vocabulary other than the framework's roles
    vocabulary before it is written to ``Contribution.roles`` (FR-032, design review
    SPEC-001).

    This is the backstop, not the first line of defence. A person filling in a form -
    the roles field on ``MeasurementContributionInline``, ``SampleContributionInline``
    or ``UpdateContributionForm`` - hits the vocabulary restriction each narrows its
    ``roles`` queryset to first, as an ordinary field validation error attached to the
    form. This receiver exists for every write path that never goes through one of
    those forms at all - a fixture, a management command, a raw ``roles.add()`` call -
    where there is no form to narrow and nothing else stops an off-vocabulary concept
    reaching the through table. Raising here, uncaught, is acceptable for that kind of
    caller; it would not be for a form submission, which is why the admin surfaces
    narrow their querysets instead of relying on this alone.

    Connected to ``m2m_changed`` for ``Contribution.roles.through`` with
    ``action="pre_add"``. That single action covers both ``roles.add()`` directly and
    the additive half of ``roles.set()`` - Django's ``ManyRelatedManager.set()``
    resolves into a ``remove()`` for ids no longer wanted and an ``add()`` for the new
    ones, and it is that internal ``add()`` that sends this signal. Raising here happens
    before Django's ``bulk_create`` of the through rows runs, and the surrounding
    ``add()``/``set()`` call is itself inside a transaction, so nothing in the same call
    is written - not the offending role, and not any other role passed alongside it.

    ``reverse=True`` would mean the write came from the concept side (a
    ``Concept`` instance's own manager adding itself to contributions).
    ``ConceptManyToManyField`` (``RelatedConceptMixin.__init__``) hard-codes
    ``related_name="+"`` for every field it creates, including ``Contribution.roles``,
    so no reverse accessor exists at all. That direction is not reachable through the
    ORM's public surface, so it is left unhandled here rather than guarded against.
    """
    if action != "pre_add" or reverse or not pk_set:
        return

    from .models import CONTRIBUTION_ROLES_VOCABULARY_MESSAGE

    if (
        model.objects.filter(pk__in=pk_set)
        .exclude(vocabulary__name="fairdm-roles")
        .exists()
    ):
        raise ValidationError(CONTRIBUTION_ROLES_VOCABULARY_MESSAGE)
