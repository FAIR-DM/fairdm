# How to create a plugin

A plugin adds a page to a record, such as a sample, and a tab for it in the record's navigation. You create one when your portal needs a page that belongs to a record and that FairDM does not draw.

## Before you start

You need an installed app of your portal. This guide uses an app called `myapp` and adds an **Analysis** page to every sample. Replace `myapp` with the name of your app.

## Steps

1. Create `plugins.py` in your app. FairDM imports the `plugins` module of every installed app at start-up, so no other step registers it.

2. Write the view and register it against the record type.

   ```python
   from django.utils.translation import gettext_lazy as _

   from fairdm import plugins
   from fairdm.core.sample.models import Sample
   from fairdm.plugins import Plugin
   from fairdm.views import FairDMTemplateView


   @plugins.register(Sample, label=_("Analysis"), icon="chart", order=100)
   class Analysis(Plugin, FairDMTemplateView):
       template_name = "myapp/plugins/analysis.html"
       page_title = _("Analysis")
   ```

   List `Plugin` before the view class. `label`, `icon` and `order` set the tab, as listed under Registration in [Plugins](../reference/plugins.md).

3. Create the template `myapp/templates/myapp/plugins/analysis.html`. The record is `base_object`.

   ```django
   {% extends "page_view.html" %}

   {% block page.content %}
     <p>{{ base_object }}</p>
   {% endblock page.content %}
   ```

   Fill `page.content`. If you fill the outer `content` block instead, you replace the whole page, heading and layout included.

4. To add data of your own, override `get_context_data`.

   ```python
   def get_context_data(self, **kwargs):
       context = super().get_context_data(**kwargs)
       context["summary"] = summarise(self.base_object)
       return context
   ```

5. Start the portal and open a sample.

## The result

The sample has a tab called **Analysis**, ordered by `order` among the sample's other tabs. The page is served at `/samples/<uuid>/analysis/`, and its URL name is `sample:analysis`. Reverse it from Python with the plugin helper:

```python
from fairdm.plugins import reverse

reverse(sample, "analysis")
```

The address segment is the class name, slugified. Set `url_path` to choose your own, as listed in [Plugins](../reference/plugins.md).

Everyone who can reach a sample can open the page, because the plugin states no rule. To restrict it, see [How to restrict a plugin to some users](restrict-a-plugin-to-some-users.md). To give the plugin more pages, see [How to add pages to a plugin](add-pages-to-a-plugin.md).

A plugin can be registered against a project, dataset, sample, measurement or contributor. To register it against several, give `register` each model.
