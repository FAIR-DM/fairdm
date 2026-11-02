# Changing the base views

This page is for maintainers who change the view classes in `fairdm/views/base.py`. How a portal developer uses those classes is in [Base views](../developers/reference/base-views.md), and why they are layered is in [How FairDM views are layered](../developers/explanation/how-fairdm-views-are-layered.md).

## Keep the layer thin

Each of the seven classes is django-meta's `MetadataMixin` listed ahead of one django-mvp view. Add behaviour here only when every portal view should receive it. Behaviour that belongs to one page goes in that page's view.

Three classes add nothing beyond the composition:

- `FairDMDetailView`
- `FairDMCreateView`
- `FairDMUpdateView`

`FairDMTemplateView` sets a default `template_name`. `FairDMListView` and `FairDMTableView` set `paginate_by`. `FairDMDeleteView` overrides `_collect_deletion_data`, `get_back_url` and `get_back_url_fallback` to correct how django-mvp's deletion page treats restricted relations and the `?back` address. Comments on those overrides say which upstream fix lets you remove them. Remove an override when the django-mvp version the package requires contains the fix.

## Docstrings

A change to a view's attributes, hooks or context updates its class docstring in the same change. The docstring format is set out in [Code documentation](standards/code-documentation.md).

## Tests

`tests/test_views/test_base.py` holds a concrete subclass of each of the seven classes and checks that it answers, that `meta` is in the context, and that the context carries the object or form the view promises. `FairDMTableView` has a separate test for its default page size. Add a test there for each new behaviour.
