from fairdm.core.models import Measurement, Sample
from fairdm.db import models


class CustomParentSample(Sample):
    char_field = models.CharField(
        "Character Field", max_length=200, help_text="Enter a string of up to 200 characters."
    )

    class Meta:
        verbose_name = "Rock Sample"
        verbose_name_plural = "Rock Samples"


class CustomSample(Sample):
    char_field = models.CharField(
        "Character Field", max_length=200, help_text="Enter a string of up to 200 characters.", blank=True, null=True
    )
    text_field = models.TextField("Text Field", help_text="Enter a large amount of text.", blank=True, null=True)
    integer_field = models.IntegerField("Integer Field", help_text="Enter an integer.", blank=True, null=True)
    big_integer_field = models.BigIntegerField(
        "Big Integer Field", help_text="Enter a large integer.", blank=True, null=True
    )
    positive_integer_field = models.PositiveIntegerField(
        "Positive Integer Field", help_text="Enter a positive integer.", blank=True, null=True
    )
    positive_small_integer_field = models.PositiveSmallIntegerField(
        "Positive Small Integer Field", help_text="Enter a small positive integer.", blank=True, null=True
    )
    small_integer_field = models.SmallIntegerField(
        "Small Integer Field", help_text="Enter a small integer.", blank=True, null=True
    )
    boolean_field = models.BooleanField(
        "Boolean Field", default=False, help_text="Select True or False.", blank=True, null=True
    )
    date_field = models.DateField("Date Field", help_text="Select a date.", blank=True, null=True)
    date_time_field = models.DateTimeField(
        "Date Time Field", help_text="Select a date and time.", blank=True, null=True
    )
    time_field = models.TimeField("Time Field", help_text="Select a time.", blank=True, null=True)
    decimal_field = models.DecimalField(
        "Decimal Field", max_digits=5, decimal_places=2, help_text="Enter a decimal number.", blank=True, null=True
    )
    float_field = models.FloatField("Float Field", help_text="Enter a floating point number.", blank=True, null=True)

    class Meta:
        verbose_name = "Thin Section"
        verbose_name_plural = "Thin Sections"


class ExampleMeasurement(Measurement):
    # standard django fields
    char_field = models.CharField(
        "Character Field", max_length=200, help_text="Enter a string of up to 200 characters.", blank=True, null=True
    )
    text_field = models.TextField("Text Field", help_text="Enter a large amount of text.", blank=True, null=True)
    integer_field = models.IntegerField("Integer Field", help_text="Enter an integer.", blank=True, null=True)
    big_integer_field = models.BigIntegerField(
        "Big Integer Field", help_text="Enter a large integer.", blank=True, null=True
    )
    positive_integer_field = models.PositiveIntegerField(
        "Positive Integer Field", help_text="Enter a positive integer.", blank=True, null=True
    )
    positive_small_integer_field = models.PositiveSmallIntegerField(
        "Positive Small Integer Field", help_text="Enter a small positive integer.", blank=True, null=True
    )
    small_integer_field = models.SmallIntegerField(
        "Small Integer Field", help_text="Enter a small integer.", blank=True, null=True
    )
    boolean_field = models.BooleanField(
        "Boolean Field", default=False, help_text="Select True or False.", blank=True, null=True
    )
    date_field = models.DateField("Date Field", help_text="Select a date.", blank=True, null=True)
    date_time_field = models.DateTimeField(
        "Date Time Field", help_text="Select a date and time.", blank=True, null=True
    )
    time_field = models.TimeField("Time Field", help_text="Select a time.", blank=True, null=True)
    decimal_field = models.DecimalField(
        "Decimal Field", max_digits=5, decimal_places=2, help_text="Enter a decimal number.", blank=True, null=True
    )
    float_field = models.FloatField("Float Field", help_text="Enter a floating point number.", blank=True, null=True)
