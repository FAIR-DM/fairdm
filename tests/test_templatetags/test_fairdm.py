"""Tests for ``fairdm/templatetags/fairdm.py``'s ``safe_markdown`` filter —
the template-layer entry point to ``fairdm.utils.markdown.markdownify``
(issue #266, replacing martor's ``martortags``).
"""

from django.template import Context, Template

from fairdm.templatetags.fairdm import safe_markdown
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
