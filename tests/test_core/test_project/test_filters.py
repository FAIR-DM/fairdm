"""Tests for ``ProjectFilter`` in ``fairdm.core.project.filters``."""

import pytest
from mvp_forms.widgets import TomSelectMultiple
from research_vocabs.models import Concept

from fairdm.contrib.autocomplete.fields import (
    OrganizationMultipleChoiceField,
    PersonMultipleChoiceField,
)
from fairdm.contrib.autocomplete.filters import RecordMultipleFilter
from fairdm.core.project.filters import ProjectFilter
from fairdm.core.project.models import Project
from fairdm.factories import (
    ContributionFactory,
    OrganizationFactory,
    PersonFactory,
    ProjectFactory,
)
from fairdm.utils.choices import Visibility


@pytest.fixture
def keywords():
    """Two keywords from the vocabulary the project list filters on."""
    return list(Concept.objects.filter(vocabulary__name="fairdm-roles")[:2])


@pytest.fixture
def projects(keywords):
    """Three public projects: one carrying both keywords, and one carrying each."""
    first, second = keywords
    carrying = {"both": [first, second], "first": [first], "second": [second]}
    projects = {}
    for name, terms in carrying.items():
        projects[name] = ProjectFactory(visibility=Visibility.PUBLIC)
        projects[name].keywords.set(terms)
    return projects


@pytest.mark.django_db
class TestKeywordFilterControl:
    def test_the_vocabulary_filter_is_a_counted_control_with_no_autocomplete_light_widget(
        self,
    ):
        widget = ProjectFilter().filters["keywords_FairDMRoles"].field.widget

        assert isinstance(widget, TomSelectMultiple)
        assert widget.counted is True
        assert not type(widget).__module__.startswith("dal")

    def test_the_keywords_are_chosen_from_the_vocabulary_the_filter_names(
        self, keywords
    ):
        keywords[0].projects.add(ProjectFactory(visibility=Visibility.PUBLIC))

        field = ProjectFilter().filters["keywords_FairDMRoles"].field

        assert list(field.queryset) == [keywords[0]]


@pytest.mark.django_db
class TestKeywordFilter:
    def test_two_keywords_keep_only_projects_carrying_both(self, keywords, projects):
        filterset = ProjectFilter(
            data={"keywords_FairDMRoles": [keyword.pk for keyword in keywords]},
            queryset=Project.objects.all(),
        )

        assert filterset.is_valid()
        assert list(filterset.qs) == [projects["both"]]

    def test_one_keyword_keeps_every_project_carrying_it(self, keywords, projects):
        filterset = ProjectFilter(
            data={"keywords_FairDMRoles": [keywords[0].pk]},
            queryset=Project.objects.all(),
        )

        assert filterset.is_valid()
        assert set(filterset.qs) == {projects["both"], projects["first"]}

    def test_two_keywords_narrow_the_list_when_no_vocabulary_is_configured(
        self, settings, keywords, projects
    ):
        settings.FAIRDM_PROJECT = {"keywords": []}

        filterset = ProjectFilter(
            data={"keywords": [keyword.pk for keyword in keywords]},
            queryset=Project.objects.all(),
        )

        assert filterset.is_valid()
        assert list(filterset.qs) == [projects["both"]]


@pytest.mark.django_db
class TestOwnerAndContributorFilters:
    def test_the_owner_filter_is_an_organization_record_filter_at_public_scope(self):
        owner = ProjectFilter().filters["owner"]

        assert isinstance(owner, RecordMultipleFilter)
        assert owner.field_class is OrganizationMultipleChoiceField
        assert owner.field.scope == "public"

    def test_the_contributor_filter_is_a_person_record_filter_at_public_scope(self):
        contributor = ProjectFilter().filters["contributor"]

        assert isinstance(contributor, RecordMultipleFilter)
        assert contributor.field_class is PersonMultipleChoiceField
        assert contributor.field.scope == "public"

    def test_two_ticked_owners_keep_the_projects_of_either(self, in_request):
        request = in_request(PersonFactory())
        first, second, third = (OrganizationFactory() for _ in range(3))
        kept = [
            ProjectFactory(owner=first, visibility=Visibility.PUBLIC),
            ProjectFactory(owner=second, visibility=Visibility.PUBLIC),
        ]
        ProjectFactory(owner=third, visibility=Visibility.PUBLIC)

        filterset = ProjectFilter(
            data={"owner": [first.pk, second.pk]},
            queryset=Project.objects.all(),
            request=request,
        )

        assert filterset.form.is_valid(), filterset.form.errors
        assert set(filterset.qs) == set(kept)

    def test_two_ticked_contributors_keep_the_projects_of_either(self, in_request):
        request = in_request(PersonFactory())
        first, second, third = (PersonFactory() for _ in range(3))
        kept = []
        for person in (first, second, third):
            project = ProjectFactory(visibility=Visibility.PUBLIC)
            ContributionFactory(content_object=project, contributor=person)
            if person is not third:
                kept.append(project)

        filterset = ProjectFilter(
            data={"contributor": [first.pk, second.pk]},
            queryset=Project.objects.all(),
            request=request,
        )

        assert filterset.form.is_valid(), filterset.form.errors
        assert set(filterset.qs) == set(kept)
