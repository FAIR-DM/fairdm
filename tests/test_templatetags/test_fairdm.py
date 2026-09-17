"""Tests for ``fairdm/templatetags/fairdm.py``'s ``safe_markdown`` filter —
the template-layer entry point to ``fairdm.utils.markdown.markdownify``
(issue #266, replacing martor's ``martortags``).
"""

import pytest
from django.template import Context, Template

from fairdm.factories import PersonFactory
from fairdm.templatetags.fairdm import has_permission, safe_markdown
from fairdm.utils.markdown import markdownify


class TestSafeMarkdown:
    def test_renders_through_markdownify(self):
        content = "**bold** and <script>alert(1)</script>"

        assert safe_markdown(content) == markdownify(content)

    def test_template_engine_does_not_double_escape_the_output(self):
        template = Template("{% load fairdm %}{{ content|safe_markdown }}")
        rendered = template.render(Context({"content": "**bold**"}))

        assert "<strong>bold</strong>" in rendered
        assert "&lt;strong&gt;" not in rendered


@pytest.mark.django_db
class TestHasPermissionTag:
    """T018, FR-019: a rights decision made by asking the permission system, not by
    matching a group's name. Has no call site in this repository (a public template tag
    for a consuming portal), so exercised directly rather than through a page."""

    def test_a_permission_named_in_the_context_list_is_admitted(self):
        assert has_permission({"user_permissions": ["dataset.change_dataset"]}, "dataset.change_dataset")

    def test_no_user_in_context_is_refused(self):
        assert not has_permission({}, "dataset.change_dataset")

    def test_belonging_to_a_group_named_data_administrators_grants_nothing_on_its_own(self):
        from django.contrib.auth.models import Group

        legacy_named_group = Group.objects.create(name="Data Administrators")
        member = PersonFactory()
        member.groups.add(legacy_named_group)

        assert not has_permission({"user": member}, "dataset.change_dataset")

    def test_a_person_actually_holding_the_permission_is_admitted(self):
        from django.contrib.auth.models import Permission

        person = PersonFactory()
        person.user_permissions.add(
            Permission.objects.get(
                content_type__app_label="dataset", codename="change_dataset"
            )
        )

        assert has_permission({"user": person}, "dataset.change_dataset")
