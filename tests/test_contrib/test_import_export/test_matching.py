"""The matcher pairs a file's headings with the columns of a record type."""

from types import SimpleNamespace

import pytest
from fairdm.contrib.import_export.matching import HeadingMatcher

from fairdm.contrib.import_export.models import ImportJob


@pytest.fixture
def rock_matcher(rock_config):
    """The matcher of the rock sample type."""
    return HeadingMatcher(rock_config.get_table_schema())


@pytest.fixture
def xrf_matcher(xrf_config):
    """The matcher of the XRF measurement type."""
    return HeadingMatcher(xrf_config.get_table_schema())


def job_of(column_map, mode=ImportJob.Mode.BOTH):
    """Return what the matcher reads of a job: its headings, matches and mode."""
    return SimpleNamespace(headers=list(column_map), column_map=column_map, mode=mode)


class TestHeadingMatcher:
    """Matching the headings of a file to columns."""

    class TestNormalise:
        """What two headings must share to be the same."""

        @pytest.mark.parametrize(
            "heading",
            ["Rock type", "rock_type", "ROCK-TYPE", " rock  type ", "rock.type"],
        )
        def test_case_spaces_and_punctuation_are_ignored(self, heading):
            assert HeadingMatcher.normalise(heading) == "rocktype"

        def test_a_missing_heading_is_empty(self):
            assert HeadingMatcher.normalise(None) == ""

    class TestMatchHeading:
        """One heading, one column."""

        def test_the_field_name_matches(self, rock_matcher):
            assert rock_matcher.match("local_id").name == "local_id"

        def test_the_label_matches(self, rock_matcher):
            assert rock_matcher.match("Portal ID").name == "portal_id"

        def test_the_label_without_its_unit_matches(self, icp_config):
            matcher = HeadingMatcher(icp_config.get_table_schema())

            assert matcher.match("Concentration").name == "concentration_ppb"

        def test_the_label_with_its_unit_matches(self, icp_config):
            matcher = HeadingMatcher(icp_config.get_table_schema())

            assert matcher.match("Concentration (ppb)").name == "concentration_ppb"

        def test_an_alias_matches(self, rock_matcher):
            assert rock_matcher.match("Record ID").name == "portal_id"

        @pytest.mark.parametrize("heading", ["LOCAL ID", "local-id", "Local_ID"])
        def test_case_and_punctuation_do_not_matter(self, rock_matcher, heading):
            assert rock_matcher.match(heading).name == "local_id"

        def test_an_unknown_heading_matches_nothing(self, rock_matcher):
            assert rock_matcher.match("Favourite colour") is None

        def test_a_blank_heading_matches_nothing(self, rock_matcher):
            assert rock_matcher.match("  ") is None

        def test_a_column_written_on_export_only_is_not_matched(self, xrf_matcher):
            assert xrf_matcher.match("sample_name") is None

        def test_sample_id_on_a_measurement_file_goes_to_local_id(self, xrf_matcher):
            assert xrf_matcher.match("Sample ID").name == "local_id"

        def test_sample_matches_the_sample_column_of_a_measurement(self, xrf_matcher):
            assert xrf_matcher.match("Sample").name == "sample"

    class TestMatchColumns:
        """Every heading of a file at once."""

        def test_each_heading_gets_its_column_name(self, rock_matcher):
            matched = rock_matcher.match_columns(["Name", "Local ID", "Nonsense"])

            assert matched == {"Name": "name", "Local ID": "local_id", "Nonsense": ""}

        def test_the_first_of_two_headings_for_one_column_takes_it(self, rock_matcher):
            matched = rock_matcher.match_columns(["Local ID", "Sample ID"])

            assert matched == {"Local ID": "local_id", "Sample ID": ""}

    class TestMappingProblems:
        """What stops the matched columns from being checked."""

        def test_a_file_with_nothing_matched_has_a_problem(self, rock_matcher):
            assert rock_matcher.problems(job_of({"x": ""}))

        def test_a_new_record_needs_its_required_columns(self, rock_matcher):
            required = [c.name for c in rock_matcher.schema.required]
            assert required, "the rock type has a required column"
            kept = {"local_id": "local_id"}

            assert rock_matcher.problems(job_of(kept))

        def test_every_required_column_matched_leaves_no_problem(self, rock_matcher):
            matched = {c.name: c.name for c in rock_matcher.schema.required}
            matched["Local ID"] = "local_id"

            assert rock_matcher.problems(job_of(matched)) == []

        def test_only_updating_does_not_need_the_required_columns(self, rock_matcher):
            job = job_of({"Local ID": "local_id"}, mode=ImportJob.Mode.UPDATE)

            assert rock_matcher.problems(job) == []

        def test_updating_needs_an_identifier(self, rock_matcher):
            job = job_of({"Name": "name"}, mode=ImportJob.Mode.UPDATE)

            assert rock_matcher.problems(job)

        def test_a_portal_id_is_enough_to_update(self, rock_matcher):
            job = job_of({"Portal ID": "portal_id"}, mode=ImportJob.Mode.UPDATE)

            assert rock_matcher.problems(job) == []

        def test_two_headings_matched_to_one_column_is_a_problem(self, rock_matcher):
            matched = {c.name: c.name for c in rock_matcher.schema.required}
            matched["Local ID"] = "local_id"
            matched["Field ID"] = "local_id"

            assert rock_matcher.problems(job_of(matched))

    class TestMappingWarnings:
        """What is worth saying, though the file can still be checked."""

        def test_adding_with_no_identifier_warns(self, rock_matcher):
            assert rock_matcher.warnings(job_of({"Name": "name"}))

        def test_updating_with_no_identifier_does_not_warn_about_repeats(
            self, rock_matcher
        ):
            job = job_of({"Name": "name"}, mode=ImportJob.Mode.UPDATE)

            assert rock_matcher.warnings(job) == []

        def test_an_identifier_silences_the_warning(self, rock_matcher):
            assert rock_matcher.warnings(job_of({"Local ID": "local_id"})) == []

        def test_adding_only_with_no_identifier_does_not_warn(self, rock_matcher):
            job = job_of({"Name": "name"}, mode=ImportJob.Mode.ADD)

            assert rock_matcher.warnings(job) == []

        def test_latitude_without_longitude_warns(self, rock_matcher):
            matched = {"Local ID": "local_id", "Latitude": "latitude"}

            assert rock_matcher.warnings(job_of(matched))

        def test_both_coordinates_do_not_warn(self, rock_matcher):
            matched = {
                "Local ID": "local_id",
                "Latitude": "latitude",
                "Longitude": "longitude",
            }

            assert rock_matcher.warnings(job_of(matched)) == []

    class TestNeedsMatching:
        """When the person must look at the matching (FR-009)."""

        @pytest.fixture
        def whole(self, rock_matcher):
            """A column map with every required column matched, and an identifier."""
            matched = {c.name: c.name for c in rock_matcher.schema.required}
            matched["Local ID"] = "local_id"
            return matched

        def test_every_heading_matched_and_nothing_wrong_skips_it(
            self, rock_matcher, whole
        ):
            assert rock_matcher.needs_matching(job_of(whole)) is False

        def test_a_heading_with_no_column_needs_the_person(self, rock_matcher, whole):
            assert rock_matcher.needs_matching(job_of({**whole, "Extra": ""}))

        def test_a_problem_needs_the_person(self, rock_matcher):
            assert rock_matcher.needs_matching(job_of({"Local ID": "local_id"}))
