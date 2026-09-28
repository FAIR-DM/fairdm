"""Autocomplete views for FairDM models."""

from dal import autocomplete
from django.db.models import Q
from research_vocabs.models import Concept

from fairdm.contrib.contributors.models import Contribution, Contributor, Organization


class ConceptAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for Concept model with vocabulary filtering.

    This view allows filtering concepts by vocabulary to support large vocabularies
    efficiently without loading all concepts into the browser.

    Usage in forms:
        from dal import autocomplete

        field = forms.ModelMultipleChoiceField(
            queryset=Concept.objects.all(),
            widget=autocomplete.ModelSelect2Multiple(
                url='concept-autocomplete',
                forward=['vocabulary_name']  # Pass vocabulary name from another field
            )
        )

    Or with vocabulary specified in URL:
        widget=autocomplete.ModelSelect2Multiple(
            url='concept-autocomplete?vocabulary=gcmd-science-keywords'
        )
    """

    def get_queryset(self):
        """Return concepts filtered by vocabulary and search term, for signed-in users only."""
        if not self.request.user.is_authenticated:
            return Concept.objects.none()

        qs = Concept.objects.all()

        # No vocabulary is forwarded when DAL loads a field's initial values.
        vocabulary = self.forwarded.get("vocabulary", None)
        if not vocabulary:
            vocabulary = self.request.GET.get("vocabulary", None)

        if vocabulary:
            qs = qs.filter(vocabulary__name=vocabulary)

        if self.q:
            qs = qs.filter(Q(label__icontains=self.q) | Q(name__icontains=self.q))

        return qs.order_by("label")


class ContributorAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for Contributor model with filtering to exclude existing contributors.

    This view allows searching for contributors while optionally excluding those
    already associated with a specific object.

    Usage in forms:
        from dal import autocomplete, forward

        field = forms.ModelMultipleChoiceField(
            queryset=Contributor.objects.all(),
            widget=autocomplete.ModelSelect2Multiple(
                url='autocomplete:contributor',
                forward=(
                    forward.Const(str(base_object.pk), 'object_id'),
                    forward.Const(ContentType.objects.get_for_model(base_object).pk, 'content_type_id'),
                )
            )
        )
    """

    def get_queryset(self):
        """Return contributors matching the search term, minus those already on the forwarded object."""
        if not self.request.user.is_authenticated:
            return Contributor.objects.none()

        qs = Contributor.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        print(f"DEBUG: forwarded = {self.forwarded}")
        print(f"DEBUG: request.GET = {dict(self.request.GET)}")

        object_id = self.forwarded.get("object_id", None)
        content_type_id = self.forwarded.get("content_type_id", None)

        print(f"DEBUG: object_id = {object_id}, content_type_id = {content_type_id}")

        if object_id and content_type_id:
            existing_contributor_ids = Contribution.objects.filter(
                object_id=object_id, content_type_id=content_type_id
            ).values_list("contributor_id", flat=True)

            print(f"DEBUG: existing_contributor_ids = {list(existing_contributor_ids)}")

            qs = qs.exclude(pk__in=existing_contributor_ids)

        return qs.order_by("name")


class OrganizationAutocomplete(autocomplete.Select2QuerySetView):
    """Autocomplete view for Organization model.

    This view allows searching for organizations by name.

    Usage in forms:
        from dal import autocomplete

        field = forms.ModelChoiceField(
            queryset=Organization.objects.all(),
            widget=autocomplete.ModelSelect2(url='autocomplete:organization')
        )
    """

    def get_queryset(self):
        """Return organizations matching the search term, for signed-in users only."""
        if not self.request.user.is_authenticated:
            return Organization.objects.none()

        qs = Organization.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs.order_by("name")

    def get_result_label(self, result):
        """Return the label to display for each result."""
        return result.label or result.name
