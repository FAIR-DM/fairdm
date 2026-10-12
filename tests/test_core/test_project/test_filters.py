"""Tests for ``ProjectFilter`` in ``fairdm.core.project.filters``."""

import pytest
from research_vocabs.models import Concept

from fairdm.core.project.filters import ProjectFilter
from fairdm.core.project.models import Project
from fairdm.factories import ProjectFactory
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
