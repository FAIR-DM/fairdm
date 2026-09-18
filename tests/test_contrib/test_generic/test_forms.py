"""Tests for fairdm/contrib/generic/forms.py."""

import pytest

from fairdm.contrib.generic.forms import DescriptionForm
from fairdm.core.abstract import DESCRIPTION_MAX_LENGTH


@pytest.mark.django_db
class TestDescriptionForm:
    """Issue #329: the sample descriptions page saves through this
    ``ModelForm``, which runs ``full_clean()`` on the instance - the model's
    ceiling is enforced here, and the form declares the same length so the
    rejection happens before a save is attempted."""

    def test_value_at_the_ceiling_is_valid(self):
        form = DescriptionForm(
            data={"type": "SampleCollection", "value": "x" * DESCRIPTION_MAX_LENGTH}
        )

        assert form.is_valid(), form.errors

    def test_value_one_character_over_the_ceiling_is_rejected(self):
        form = DescriptionForm(
            data={
                "type": "SampleCollection",
                "value": "x" * (DESCRIPTION_MAX_LENGTH + 1),
            }
        )

        assert not form.is_valid()
        assert "value" in form.errors
