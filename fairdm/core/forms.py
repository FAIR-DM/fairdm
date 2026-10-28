"""Base form, the manager-only fields mixin, the keyword form and the concept drop-down shared by the core forms."""

import copy
from typing import ClassVar

from controlled_vocabularies.forms import DeclinesAdminRelatedWrapperMixin
from crispy_forms.helper import FormHelper
from django.forms import ModelChoiceField, ModelForm, Select
from django.forms.models import ModelChoiceIterator
from django.utils.translation import gettext_lazy as _

from fairdm.contrib.autocomplete.fields import TagsField

from .vocabularies import collection_members


class ManagerOnlyFieldsMixin:
    """Leave the fields that decide who gets into a record out of its form, for anyone who cannot manage it.

    Visibility and the record a record sits under (a project's owner, a dataset's project, a
    sample's or measurement's dataset) change who holds rights over it, so only someone who can
    manage it is offered them. A form for a new record leaves nothing out.

    Attributes:
        manager_only_fields: The names of the fields to leave out.
    """

    manager_only_fields: tuple[str, ...] = ()

    def withhold_manager_only_fields(self, request):
        """Remove the manager-only fields unless the request's user can manage the record.

        Args:
            request: The current request, or None, which counts as someone who cannot manage it.
        """
        from fairdm.contrib.contributors.access import RecordAccess

        user = getattr(request, "user", None)
        if self.instance.pk is None or (
            user is not None and RecordAccess(self.instance).can_manage(user)
        ):
            return
        for name in self.manager_only_fields:
            self.fields.pop(name, None)


class BaseForm(ModelForm):
    """Model form that accepts the request and drops declared fields missing from ``Meta.fields``.

    Args:
        *args: Positional arguments passed to ``ModelForm``.
        **kwargs: Keyword arguments passed to ``ModelForm``. ``request`` is removed first and
            sets ``self.request`` and ``self.user``.
    """

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        self.user = None
        if self.request:
            self.user = self.request.user

        super().__init__(*args, **kwargs)
        allowed = set(self._meta.fields)
        for name in list(self.fields):
            if name not in allowed:
                del self.fields[name]


class KeywordForm(ModelForm):
    """Edit a record's free keywords: words a person types, with no vocabulary behind them.

    Keywords chosen from a controlled vocabulary are not offered here and are left as they are
    when the form is saved.

    Args:
        *args: Passed to ``ModelForm``.
        **kwargs: Passed to ``ModelForm``. The model is taken from ``instance`` when given.
    """

    class Meta:
        fields: ClassVar[list[str]] = []

    def __init__(self, *args, **kwargs):
        instance = kwargs.get("instance")
        if instance:
            # A copy, so building the form for one model never rebinds the class for the next.
            self._meta = copy.copy(self._meta)
            self._meta.model = type(instance)

        super().__init__(*args, **kwargs)

        self.fields["tags"] = TagsField(
            label=_("Free keywords"),
            help_text=_("Words this record should be found under."),
            required=False,
            allow_new=True,
        )
        if self.instance.pk:
            self.initial["tags"] = list(self.instance.tags.names())

        self.helper = FormHelper()
        self.helper.form_id = "keyword-form"

    def save(self, commit=True):
        """Save the free keywords, leaving the record's vocabulary keywords alone."""
        instance = super().save(commit=False)

        if commit:
            instance.save()
            instance.tags.set(self.cleaned_data["tags"])

        return instance


class CollectionOrderIterator(ModelChoiceIterator):
    """Yield a concept field's choices in the order of the collection it is limited to.

    A field with no collection lists its concepts by name.
    """

    def __iter__(self):
        """Yield the empty choice, then one choice per concept."""
        if self.field.empty_label is not None:
            yield ("", self.field.empty_label)
        concepts = list(self.queryset)
        collection = getattr(self.field.model_field, "collection", None)
        if collection:
            order = [concept.uri for concept in collection_members(collection)]
            concepts.sort(
                key=lambda c: order.index(c.uri) if c.uri in order else len(order)
            )
        else:
            concepts.sort(key=lambda c: c.display_label().casefold())
        for concept in concepts:
            yield self.choice(concept)


class ConceptSelectField(DeclinesAdminRelatedWrapperMixin, ModelChoiceField):
    """A concept field drawn as a drop-down of the concepts it offers.

    For a short, closed list such as the description, date and identifier types, in place of
    the search box a concept field renders by default. Pass it as the ``form_class`` of a
    ``ConceptField``'s form field. Each concept is shown by its name in the reading language.

    Args:
        *args: Passed to ``ModelChoiceField``.
        model_field: The ``ConceptField`` the form field was built from.
        **kwargs: Passed to ``ModelChoiceField``.
    """

    iterator = CollectionOrderIterator

    def __init__(self, *args, model_field=None, **kwargs):
        self.model_field = model_field
        kwargs.setdefault("widget", Select)
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        """Return the concept's name in the reading language."""
        return obj.display_label()
