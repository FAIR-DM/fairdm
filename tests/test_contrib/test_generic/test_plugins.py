"""``DescriptionsPlugin`` and ``KeyDatesPlugin`` declared no ``template_name``, so template
resolution fell through to ``InlineFormSetView``'s inherited ``_detail`` suffix and served the
record's own detail page in its place. Both returned 200, and the formset was never drawn
(issue #280) — status alone does not catch this, so these assert the template.

Selecting the right template was not sufficient by itself: ``plugins/key-dates.html`` extended
``fairdm/plugin.html`` under a ``{% block plugin %}`` that the parent chain never defines (the
block it needed is ``page.content``), so its content was silently dropped and the page showed the
parent's own "Coming soon..." placeholder. A template-name assertion alone would not have caught
that, so these also assert the formset itself is on the page.
"""

import pytest
from django.urls import reverse
from guardian.shortcuts import assign_perm

from fairdm.core.utils import assign_perm as assign_sample_perm
from fairdm.factories import DatasetFactory, UserFactory
from fairdm_demo.factories import RockSampleFactory


@pytest.mark.django_db
class TestManagementPagesRenderTheirOwnTemplate:
    def test_dataset_descriptions_page_renders_the_descriptions_form(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        response = client.get(
            reverse("dataset:descriptions", kwargs={"uuid": dataset.uuid})
        )
        template_names = [t.name for t in response.templates if t.name]
        assert "plugins/descriptions.html" in template_names
        assert "dataset/dataset_detail.html" not in template_names
        content = response.content.decode()
        assert "Coming soon" not in content
        assert 'id="descriptions-form"' in content

    def test_dataset_key_dates_page_renders_the_key_dates_form(self, client):
        user = UserFactory()
        dataset = DatasetFactory()
        assign_perm("change_dataset", user, dataset)
        client.force_login(user)
        response = client.get(reverse("dataset:key-dates", kwargs={"uuid": dataset.uuid}))
        template_names = [t.name for t in response.templates if t.name]
        assert "plugins/key-dates.html" in template_names
        assert "dataset/dataset_detail.html" not in template_names
        content = response.content.decode()
        assert "Coming soon" not in content
        assert "key-dates-form" in content

    def test_sample_descriptions_page_renders_the_descriptions_form(self, client):
        user = UserFactory()
        sample = RockSampleFactory()
        assign_sample_perm("change_sample", user, sample)
        client.force_login(user)
        response = client.get(
            reverse("sample:basic-information", kwargs={"uuid": sample.uuid})
        )
        template_names = [t.name for t in response.templates if t.name]
        assert "plugins/descriptions.html" in template_names
        content = response.content.decode()
        assert "Coming soon" not in content
        assert 'id="descriptions-form"' in content

    def test_sample_key_dates_page_renders_the_key_dates_form(self, client):
        user = UserFactory()
        sample = RockSampleFactory()
        assign_sample_perm("change_sample", user, sample)
        client.force_login(user)
        response = client.get(reverse("sample:key-dates", kwargs={"uuid": sample.uuid}))
        template_names = [t.name for t in response.templates if t.name]
        assert "plugins/key-dates.html" in template_names
        content = response.content.decode()
        assert "Coming soon" not in content
        assert "key-dates-form" in content
