# Held fix: T019b

Not applied, because it makes `tests/test_contrib/test_plugins/test_base.py::TestBaseOverviewPlugin::test_overview_plugin_provides_context`
fail (see decisions.md D25). Apply it together with a change to that test.

## fairdm/contrib/plugins/checks.py, in `validate_places_offered`

Replace

```python
    if any(issubclass(mount.plugin_class, OverviewPlaces) for mount in mounts):
        return
```

with

```python
    drawing = [
        mount.plugin_class
        for mount in mounts
        if issubclass(mount.plugin_class, OverviewPlaces)
    ]
    if len(drawing) > 1:
        fail_between(
            drawing,
            model,
            "are both built on OverviewPlaces, but a record type has one overview that draws "
            "page actions and cards; replace the overview with replaces= instead of "
            "registering a second",
        )
    if drawing:
        return
```

and say in its docstring that only one plugin may be built on `OverviewPlaces`, and that a
replacement of the overview is the same mount.

## tests/test_contrib/test_plugins/test_places.py, before `TestServedUnderAMount`

```python
class RivalOverview(OverviewPlaces, Plugin, TemplateView):
    template_name = "base.html"


class ReplacementOverview(SomeOverview):
    pass


class TestRecordTypeHasOneOverviewDrawingPlaces:
    def test_a_record_type_with_two_plugins_built_on_overview_places_is_refused(
        self, fresh
    ):
        fresh.register(Sample)(SomeOverview)
        fresh.register(Sample)(RivalOverview)

        with pytest.raises(PluginRegistrationError) as excinfo:
            fresh.validate_all()

        message = str(excinfo.value)
        assert "SomeOverview" in message
        assert "RivalOverview" in message
        assert "Sample" in message

    def test_a_record_type_with_one_is_accepted(self, fresh):
        fresh.register(Sample)(SomeOverview)
        fresh.register(Sample)(AlphaPage)

        fresh.validate_all()

    def test_a_replacement_of_the_overview_is_not_a_second(self, fresh):
        fresh.register(Sample)(SomeOverview)
        fresh.register(Sample, replaces=SomeOverview)(ReplacementOverview)

        fresh.validate_all()

        assert [m.plugin_class for m in fresh.resolve(Sample)] == [ReplacementOverview]

    def test_two_record_types_may_each_have_one(self, fresh):
        fresh.register(Sample)(SomeOverview)
        fresh.register(Dataset)(RivalOverview)

        fresh.validate_all()


```

## Documentation to add with it

- decisions.md D13: a line saying a record type that registers a second overview is now refused.
- docs/portal-development/create_a_plugin.md, "When a registration is wrong": a record type with
  two plugins built on `OverviewPlaces`, refused with both named; a replacement of the overview is
  not a second.
