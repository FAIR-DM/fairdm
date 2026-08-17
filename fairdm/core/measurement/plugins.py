"""Measurements have no plugin surface.

A measurement is a component of the sample page rather than a record with a page of its own, so it
has no local navigation and nothing to attach a plugin to. Five plugins were registered here and
none of them could ever be served.

If measurements gain their own page, register plugins against them here and declare the record's
addressing in the measurement URL configuration.
"""
