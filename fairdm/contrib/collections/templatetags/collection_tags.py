from django import template

# import flatattrs

register = template.Library()

field_map = {
    "CharField": "char",
    "TextField": "char",
    "IntegerField": "num",
    "BigIntegerField": "num",
    "PositiveIntegerField": "num",
    "PositiveSmallIntegerField": "num",
    "SmallIntegerField": "num",
    "BooleanField": "bool",
    "DateField": "date",
    "DateTimeField": "datetime",
    "TimeField": "time",
    "DecimalField": "num",
    "FloatField": "num",
    "ForeignKey": "rel",
    "ManyToManyField": "rel",
}


@register.filter
def get_column_classes(col):
    """Renders HTML of the specified unit"""
    table = col._table
    model = table._meta.model
    fname = col.accessor
    field_type = ""
    try:
        db_field = model._meta.get_field(fname)
        field_type = db_field.get_internal_type()
    except Exception:
        field_type = "CharField"

    return f"{field_map.get(field_type, 'char')} {col.accessor.replace('_', '-')}"
