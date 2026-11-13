"""Tests for the citation value and its BibTeX and RIS writers."""

import codecs
from types import SimpleNamespace

import latexcodec  # noqa: F401  (registers the "ulatex" codec)
import pytest
import rispy
from literature.importers.bibtex import ENTRY_TYPE_TABLE
from literature.importers.ris import REFERENCE_TYPE_TABLE
from literature.models import Name
from pybtex.database import parse_string

from fairdm.core.citation import FORMATS, Citation, CitedName, publication_types


class Contributor(SimpleNamespace):
    """A contributor stand-in: a person has name parts, an organisation only a string form."""

    def __str__(self):
        return self.label


def build(**overrides):
    values = {
        "key": "P-123",
        "authors": [CitedName(family="Keller", given="Anna")],
        "year": 2024,
        "title": "Seismic survey",
        "publisher": "Acme Data Portal",
        "doi": None,
        "url": "https://portal.example/p/P-123/",
        "bibtex_type": "misc",
        "ris_type": "GEN",
    }
    values.update(overrides)
    return Citation(**values)


def read_bibtex(text):
    """Parse ``text`` with pybtex and return the one entry it must hold."""
    data = parse_string(text, "bibtex")
    assert len(data.entries) == 1
    return next(iter(data.entries.values()))


def read_field(entry, name):
    return codecs.decode(entry.fields[name], "ulatex")


def read_ris(text):
    entries = rispy.loads(text)
    assert len(entries) == 1
    return entries[0]


class TestCitedName:
    def test_from_contributor_a_person_gives_family_and_given(self):
        person = Contributor(last_name="Keller", first_name="Anna", label="Anna Keller")

        assert CitedName.from_contributor(person) == CitedName(family="Keller", given="Anna")

    def test_from_contributor_an_organisation_gives_its_string_form(self):
        organisation = Contributor(label="Acme Lab")

        assert CitedName.from_contributor(organisation) == CitedName(literal="Acme Lab")

    def test_from_item_name_gives_family_and_given(self):
        name = Name(family="Keller", given="Anna")

        assert CitedName.from_item_name(name) == CitedName(family="Keller", given="Anna")

    def test_from_item_name_a_literal_name_stays_one_name(self):
        name = Name(literal="Acme Lab")

        assert CitedName.from_item_name(name) == CitedName(literal="Acme Lab")

    def test_from_item_name_puts_the_particle_before_the_family_name_and_keeps_the_suffix(self):
        name = Name(family="Beethoven", given="Ludwig", non_dropping_particle="van", suffix="Jr.")

        assert CitedName.from_item_name(name) == CitedName(
            family="van Beethoven", given="Ludwig", suffix="Jr."
        )


class TestCitation:
    class TestToBibtex:
        def test_one_entry_with_type_key_and_fields(self):
            citation = build(
                authors=[
                    CitedName(family="Keller", given="Anna"),
                    CitedName(family="Brandt", given="Lena", suffix="Jr."),
                ],
                doi="10.1000/abc",
                url="https://doi.org/10.1000/abc",
                bibtex_type="dataset",
            )

            entry = read_bibtex(citation.to_bibtex())

            assert entry.type == "dataset"
            assert [(p.last_names, p.first_names, p.lineage_names) for p in entry.persons["author"]] == [
                (["Keller"], ["Anna"], []),
                (["Brandt"], ["Lena"], ["Jr."]),
            ]
            assert entry.fields["year"] == "2024"
            assert entry.fields["title"] == "Seismic survey"
            assert entry.fields["publisher"] == "Acme Data Portal"
            assert entry.fields["doi"] == "10.1000/abc"
            assert entry.fields["url"] == "https://doi.org/10.1000/abc"

        def test_the_key_is_the_records_portal_id(self):
            data = parse_string(build(key="P-123").to_bibtex(), "bibtex")

            assert list(data.entries) == ["P-123"]

        def test_no_author_field_for_nobody(self):
            entry = read_bibtex(build(authors=[]).to_bibtex())

            assert "author" not in entry.persons

        def test_no_doi_field_without_a_doi_and_no_url_field_without_a_url(self):
            entry = read_bibtex(build(doi=None, url=None).to_bibtex())

            assert "doi" not in entry.fields
            assert "url" not in entry.fields

        def test_an_organisation_stays_one_name(self):
            citation = build(authors=[CitedName(literal="Acme Lab, Inc. and Sons")])

            entry = read_bibtex(citation.to_bibtex())

            assert len(entry.persons["author"]) == 1
            assert str(entry.persons["author"][0]) == "{Acme Lab, Inc. and Sons}"

        def test_special_characters_read_back_as_written(self):
            title = "R&D 50% #2 a_b ~c"
            citation = build(title=title, publisher="Smith & Sons_#1")

            entry = read_bibtex(citation.to_bibtex())

            assert read_field(entry, "title") == title
            assert read_field(entry, "publisher") == "Smith & Sons_#1"

        def test_letters_outside_english_and_other_scripts_read_back_as_written(self):
            title = "Müller, Søren and 東京 Δ"
            citation = build(title=title, authors=[CitedName(family="Müller", given="Zoë")])

            entry = read_bibtex(citation.to_bibtex())

            assert read_field(entry, "title") == title
            assert codecs.decode(str(entry.persons["author"][0]), "ulatex") == "Müller, Zoë"

        @pytest.mark.parametrize(
            ("title", "written"),
            [
                ("a\\b", r"a\textbackslash{}b"),
                ("cost $5", r"cost \$5"),
                ("x^2", r"x\textasciicircum{}2"),
                ("a } b", r"a \textbraceright{} b"),
                ("a { b", r"a \textbraceleft{} b"),
                ("a } b { c", r"a \textbraceright{} b \textbraceleft{} c"),
                ("a {b} c", r"a \{b\} c"),
                ("}{", r"\textbraceright{}\textbraceleft{}"),
            ],
        )
        def test_a_character_tex_reads_as_a_command_is_written_as_the_command_for_it(
            self, title, written
        ):
            entry = read_bibtex(build(title=title).to_bibtex())

            assert entry.fields["title"] == written

        def test_a_doi_and_url_holding_underscore_and_hash_read_back_exactly_as_given(self):
            doi = "10.1000/abc_def#1"
            url = "https://example.org/a_b?x=1#frag_2"
            citation = build(doi=doi, url=url)

            entry = read_bibtex(citation.to_bibtex())

            assert entry.fields["doi"] == doi
            assert entry.fields["url"] == url

        def test_a_line_break_reads_back_as_a_space(self):
            entry = read_bibtex(build(title="First line\r\nsecond\n\n  line").to_bibtex())

            assert read_field(entry, "title") == "First line second line"

    class TestToRis:
        def test_one_entry_with_type_authors_and_fields(self):
            citation = build(
                authors=[
                    CitedName(family="Keller", given="Anna"),
                    CitedName(literal="Acme Lab"),
                    CitedName(family="Brandt", given="Lena", suffix="Jr."),
                ],
                doi="10.1000/abc",
                url="https://doi.org/10.1000/abc",
                ris_type="DATA",
            )

            entry = read_ris(citation.to_ris())

            assert entry["type_of_reference"] == "DATA"
            assert entry["authors"] == ["Keller, Anna", "Acme Lab", "Brandt, Lena, Jr."]
            assert entry["title"] == "Seismic survey"
            assert entry["year"] == "2024"
            assert entry["publisher"] == "Acme Data Portal"
            assert entry["doi"] == "10.1000/abc"
            assert entry["urls"] == ["https://doi.org/10.1000/abc"]

        def test_no_author_line_for_nobody(self):
            entry = read_ris(build(authors=[]).to_ris())

            assert "authors" not in entry

        def test_the_first_line_is_the_type_line(self):
            assert build(ris_type="GEN").to_ris().splitlines()[0] == "TY  - GEN"

        def test_a_line_break_reads_back_as_a_space(self):
            entry = read_ris(build(title="First line\r\nsecond\n\n  line").to_ris())

            assert entry["title"] == "First line second line"

    class TestFilename:
        def test_a_title_with_spaces_and_accents_gives_an_ascii_slug_with_the_extension(self):
            citation = build(title="Café Müller: Seismic Survey")

            assert citation.filename("bib") == "cafe-muller-seismic-survey.bib"

        def test_an_empty_title_gives_the_key(self):
            assert build(title="", key="P-123").filename("ris") == "P-123.ris"

        def test_a_long_title_is_cut_to_sixty_characters_before_the_extension(self):
            name = build(title="word " * 40).filename("bib")

            assert len(name) <= 60 + len(".bib")


class TestPublicationTypes:
    MAPPED = [
        ("article-journal", "article", "JOUR"),
        ("dataset", "dataset", "DATA"),
        ("book", "book", "BOOK"),
        ("chapter", "incollection", "CHAP"),
        ("paper-conference", "inproceedings", "CPAPER"),
        ("report", "techreport", "RPRT"),
        ("thesis", "phdthesis", "THES"),
        ("webpage", "online", "ELEC"),
        ("software", "software", "COMP"),
    ]

    @pytest.mark.parametrize(("csl", "bibtex", "ris"), MAPPED)
    def test_each_mapped_type_is_what_the_import_tables_read_back_as_the_same_csl_type(
        self, csl, bibtex, ris
    ):
        assert publication_types(csl) == (bibtex, ris)
        assert REFERENCE_TYPE_TABLE[ris] == csl
        if bibtex in ENTRY_TYPE_TABLE:
            assert ENTRY_TYPE_TABLE[bibtex].csl == csl
        else:
            # django-literature's BibTeX table has no entry for software, which biblatex
            # still calls @software; the RIS table is the independent check there.
            assert csl == "software"

    def test_an_unknown_type_gives_misc_and_gen(self):
        assert publication_types("no-such-type") == ("misc", "GEN")


class TestFormats:
    def test_the_three_formats_in_order(self):
        assert [f.key for f in FORMATS] == ["text", "bibtex", "ris"]
        assert [f.extension for f in FORMATS] == ["txt", "bib", "ris"]
        assert [f.downloadable for f in FORMATS] == [False, True, True]
        assert [f.content_type for f in FORMATS] == [
            "text/plain; charset=utf-8",
            "application/x-bibtex; charset=utf-8",
            "application/x-research-info-systems; charset=utf-8",
        ]
