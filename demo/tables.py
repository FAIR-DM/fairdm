"""Table definitions for the demo sample models."""

from fairdm.contrib.collections.tables import SampleTable

from .models import CustomSample


class CustomSampleTable(SampleTable):
    """List custom samples with one column per field type."""

    class Meta:
        model = CustomSample
        exclude = [
            "path",
            "depth",
            "status",
            "has_children",
            "has_parent",
        ]
        fields = [
            "id",
            "dataset",
            "name",
            "char_field",
            "text_field",
            "integer_field",
            "big_integer_field",
            "positive_integer_field",
            "positive_small_integer_field",
            "small_integer_field",
            "boolean_field",
            "date_field",
            "date_time_field",
            "time_field",
            "decimal_field",
            "float_field",
        ]

    def render_text_field(self, value):
        """Truncate the text field to 32 characters.

        Args:
            value: The full text value.

        Returns:
            The first 32 characters followed by an ellipsis.
        """
        return f"{value[:32]}..."

    def value_text_field(self, value):
        """Export the text field untruncated.

        Args:
            value: The full text value.

        Returns:
            The value unchanged.
        """
        return value
