"""Tests for ``fairdm/utils/markdown.py`` — the sanitising markdown renderer
that replaces martor (issue #266, GPL-3.0 incompatible with the MIT license).

django-markdownx's own ``markdownx.utils.markdownify`` is bare
``markdown.markdown(...)`` with no sanitisation, so this module supplies its
own. These tests are the point of the whole change: stored user markdown
(profile biographies, dataset/project/sample descriptions) must never carry
an executable payload into rendered HTML.
"""

from fairdm.utils.markdown import markdownify


class TestSanitisation:
    """Each case is a payload markdown can legitimately produce, that must
    not survive rendering with its executable part intact."""

    def test_script_tag_is_stripped(self):
        html = markdownify("Hello <script>alert('xss')</script> world")

        assert "<script" not in html
        assert "alert(" not in html

    def test_onerror_attribute_is_stripped(self):
        html = markdownify('Look: <img src="x" onerror="alert(1)">')

        assert "onerror" not in html

    def test_javascript_url_is_stripped(self):
        html = markdownify("[click me](javascript:alert(1))")

        assert "javascript:" not in html


class TestOrdinaryMarkdownRenders:
    """The sanitiser must not be so tight that it strips ordinary markdown
    output — this is what stops TestSanitisation from passing by accident."""

    def test_heading(self):
        html = markdownify("# Title")

        assert "<h1>Title</h1>" in html

    def test_bold(self):
        html = markdownify("**bold text**")

        assert "<strong>bold text</strong>" in html

    def test_link(self):
        html = markdownify("[FairDM](https://fairdm.org)")

        assert '<a href="https://fairdm.org"' in html
        assert ">FairDM</a>" in html

    def test_unordered_list(self):
        html = markdownify("- one\n- two")

        assert "<li>one</li>" in html
        assert "<li>two</li>" in html

    def test_code_block(self):
        html = markdownify("```\nprint('hi')\n```")

        assert "<pre>" in html
        assert "print(" in html

    def test_table(self):
        html = markdownify("| A | B |\n| - | - |\n| 1 | 2 |")

        assert "<table>" in html
        assert "<td>1</td>" in html

    def test_strikethrough(self):
        html = markdownify("~~gone~~")

        assert "<del>gone</del>" in html

    def test_bare_url_autolinks(self):
        html = markdownify("See https://fairdm.org for details")

        assert '<a href="https://fairdm.org"' in html
