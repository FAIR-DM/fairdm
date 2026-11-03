# How to give a sample or measurement type its own overview page

Every sample and measurement opens on a shared overview page that reads only the base model. You give a type its own page to show the fields only that type has. There is nothing to register: you provide one template.

## Before you start

You need a registered sample or measurement type. This guide uses a sample type `CoreSample` in an app `geochem`, with the fields `depth_m` and `lithology`. See [How to add a sample type](add-a-sample-type.md) and [How to add a measurement type](add-a-measurement-type.md).

## Steps

1. Name the template for the type: `<app_label>/<model_name>_overview.html`, in lowercase. For `CoreSample` in `geochem` it is `templates/geochem/coresample_overview.html`. A measurement type works the same way.

2. Extend the shared page. A sample type extends `sample/sample_overview.html` and a measurement type extends `measurement/measurement_overview.html`.

3. Fill `overview.properties`, which the shared page leaves empty for this. In the template, `sample` is the sample as its own type, so its fields are available.

   ```django
   {# templates/geochem/coresample_overview.html #}
   {% extends "sample/sample_overview.html" %}
   {% load i18n %}

   {# Add the lithology beside the type and status badges. #}
   {% block overview.badges %}
     {{ block.super }}
     {% if sample.lithology %}
       <span class="badge badge-outline badge-sm">{{ sample.lithology|capfirst }}</span>
     {% endif %}
   {% endblock overview.badges %}

   {% block overview.properties %}
     <c-mvp.card title="{% translate 'Core properties' %}" class="bg-base-100">
       <c-mvp.data-field label="{% translate 'Depth (m)' %}" value="{{ sample.depth_m|default_if_none:'' }}" />
       <c-mvp.data-field label="{% translate 'Lithology' %}" value="{{ sample.lithology|capfirst }}" />
     </c-mvp.card>
   {% endblock overview.properties %}
   ```

4. For a measurement type that records its result in some way other than a single `value`, also fill `overview.result`. A type that declares a `value`, and optionally an `uncertainty`, gets its result shown with no template at all.

   ```django
   {# templates/geochem/gasmeasurement_overview.html #}
   {% extends "measurement/measurement_overview.html" %}

   {% block overview.result %}
     <c-mvp.card.wrapper class="bg-base-100">
       <div class="card-body gap-3">
         <p class="text-4xl font-semibold tabular-nums">{{ measurement.concentration_ppm }} ppm</p>
       </div>
     </c-mvp.card.wrapper>
   {% endblock overview.result %}
   ```

5. Open a record of the type.

## The result

The page shows your fields and every block you did not fill: the history, the measurements, the side column and the citation. The shared page still reads only the base model.

- A subtype with no template of its own uses its parent type's template.
- A type with no template anywhere in its ancestry uses the shared page.
- To give a subtype a page of its own that keeps the parent's card, add the subtype's template and extend the parent type's template.

The template lookup is described in [Overview plugins](../reference/overview-plugins.md#typedoverviewplugin) and the blocks in [Overview page blocks](../reference/overview-page-blocks.md).
