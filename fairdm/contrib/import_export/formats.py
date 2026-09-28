"""Presents all available import/export formats."""

from import_export.formats.base_formats import TextFormat


class LaTex(TextFormat):
    """LaTeX table export format."""

    TABLIB_MODULE = "tablib.formats._latex"
    CONTENT_TYPE = "application/x-tex"
