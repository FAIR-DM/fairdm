# Configuration over code

This page explains why FairDM asks you to declare a portal, with models, registration classes and settings, rather than write its views and templates. It covers the reasoning, what it buys you and what it costs. It does not show how to register a type, which is in [How to register a sample or measurement type](../developers/how-to/register-a-sample-or-measurement-type.md), or describe each registration option, which is in [Model configuration](../developers/reference/model-configuration.md).

## The idea

A research data portal needs forms to enter data, tables and filters to find it, an API for machines, import and export, an admin and pages to read records. For each type of sample or measurement, that is the same set of parts over again, shaped by the fields of the model.

Written by hand, each part is code you maintain. A change to the model means a change to the form, the table, the filter, the serializer and the admin. Different people write the parts differently, so the portal's pages drift apart. The people best placed to describe the data are researchers, and most of them are not web developers.

FairDM moves that work into the framework. You describe your data and say how it should appear. FairDM builds the rest from the description.

## What you declare

You declare three things.

- **Models.** Your sample and measurement types are Django models that extend FairDM's base models, with the fields and validators your science needs.
- **Registration.** A short class names a model and the fields that matter for it.
- **Settings.** Values such as the database, the allowed hosts and the Redis address come from the environment and the settings layers. See [How FairDM configures a portal](how-fairdm-configures-a-portal.md).

A complete registration looks like this.

```python
from fairdm.core.models import Sample
from fairdm.db import models
from fairdm.registry import ModelConfiguration, register


class RockSample(Sample):
    rock_type = models.CharField(max_length=100)
    weight_grams = models.FloatField(null=True, blank=True)


@register
class RockSampleConfig(ModelConfiguration):
    model = RockSample
    fields = ["name", "rock_type", "weight_grams", "location"]
```

## What FairDM builds from it

From that registration FairDM builds six components: a form, a table, a filter set, an API serializer, an import and export resource and an admin class. It registers the admin class unless you already registered one of your own. The portal adds the type to its collections and navigation and serves it through the API.

You reach a component through an accessor such as `get_form_class()`, and the whole framework uses the same accessor. A change you make to one component therefore applies everywhere that component is used. The generated form and filter set also carry the framework's own mixins, so a type you register without writing either gets the same widgets and dataset scoping as one with hand-written classes. See [ADR 0006](../adr/0006-generated-components-carry-the-framework-mixins.md) and [What registering a type produces](../developers/explanation/what-registering-a-type-produces.md).

## Why FairDM works this way

**The surface follows the schema.** A model is the source of truth for the shape of the data. Components generated from it cannot disagree with it, and a field you add appears in the form, the table, the API and the export once you list it.

**Portals stay consistent and interoperable.** Every portal gets the same pages and the same API shape. A reuser who learns one FairDM portal can read another. Hand-written views would make each portal different, which is the fragmentation FairDM exists to reduce. See [FAIR data and research data infrastructure](fair-data-and-research-data-infrastructure.md).

**Researchers can build portals.** The person who knows the data usually has basic Python and no frontend training. Declaring a model needs the first and not the second. See [What FairDM is for](what-fairdm-is-for.md).

**Mistakes appear early.** A registration is checked when it is built. A field name that does not exist, a model registered twice and a field list declared beside a class that would ignore it all stop the portal at start-up with a message that names the model and the attribute. The error is not found by a visitor on the first request.

**There is less to maintain.** Fewer hand-written parts means fewer parts to update when the framework changes.

## Progressive complexity

Registration is where a portal starts, not a ceiling. You can take control of a component in steps, and each step costs only what it needs.

1. **A field list.** Name the fields once, or give a component its own list. Everything else is generated.
2. **A class for one component.** Supply your own table, form or filter set. The other components stay generated.
3. **An accessor.** Override `get_table_class()` or another accessor to build a component in code when a declaration cannot say what you need.

A component's own field list and its own class cannot both be declared, because the list could never take effect. Past registration, pages can be extended with plugins, and an overview page can be extended through its blocks and templates. These are the points the framework provides for changing its behaviour, and they exist so you do not have to copy framework code.

## What it costs

The approach has limits, and you should know them before you choose it.

- **FairDM is opinionated.** It owns the application shell, the page structure and the way records are listed and edited. If you want to assemble your own stack from independent parts, the framework is the wrong starting point.
- **The core model is fixed.** You extend samples and measurements. You do not reshape projects and datasets. See [The core data model](the-core-data-model.md).
- **A generated component is a default.** It is correct for common cases, and a case it does not fit needs one of the steps above.

## Where the principle is written down

The principle is part of the project's constitution, which states that portal developers should focus on modelling their domain and configuring behaviour, not on recreating web plumbing, routing or boilerplate frontend code (Article XIII), and that auto-generated components must derive from registered models and configuration rather than from hand-wired view logic (Article XII). Read it in the [constitution](https://github.com/FAIR-DM/fairdm/blob/main/CONSTITUTION.md).

## Related pages

- [The registry](../developers/reference/registry.md) lists how to find registered types in code.
- [Model configuration](../developers/reference/model-configuration.md) describes each option.
