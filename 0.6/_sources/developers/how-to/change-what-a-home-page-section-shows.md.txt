# How to change what a home page section shows

Each section of the landing page reads its data from one method on the home view, and every method returns only what a visitor may see. You change what a section shows by subclassing the view, for example to list more datasets or to feature chosen ones.

## Before you start

The view's attributes and methods are listed in [Home page](../reference/home-page.md#fairdmhomeview). A method you override must keep to the visitor rule: return only records a signed-out visitor may open.

## Steps

1. Subclass `FairDMHomeView` in your portal. Change a limit by setting the attribute, or replace a section's data by overriding its method.

   ```python
   # portal/views.py
   from fairdm.core.dataset.models import Dataset
   from fairdm.views.generic import FairDMHomeView


   class HomeView(FairDMHomeView):
       latest_limit = 6
       people_limit = 12

       def get_latest_datasets(self):
           return (
               Dataset.objects.get_visible()
               .with_list_data()
               .filter(published=True)
               .order_by("-modified")[: self.latest_limit]
           )
   ```

2. Route `/` to your view ahead of FairDM's URLs, in the portal's URL module.

   ```python
   # config/urls.py
   from django.urls import include, path

   from portal.views import HomeView

   urlpatterns = [
       path("", HomeView.as_view(), name="home"),
       path("", include("fairdm.conf.urls")),
   ]
   ```

3. Load a dataset with `Dataset.objects.get_visible().with_list_data()` and a project with `Project.objects.get_visible().with_list_data().with_contributors()`. A queryset without them costs extra queries for every card, because the sections draw [`c-dataset.card`](../reference/components.md#c-datasetcard) and [`c-project.card`](../reference/components.md#c-projectcard).

4. Open `/` while signed out.

## The result

The section shows the records your method returns. A section whose method returns nothing is left out of the page. To add a section instead of changing one, see [How to add a section to the home page](add-a-section-to-the-home-page.md).
