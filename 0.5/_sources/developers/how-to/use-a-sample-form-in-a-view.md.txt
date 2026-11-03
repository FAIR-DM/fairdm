# How to use a sample form in a view

This guide puts a sample form and filter set of your own into views: a create view, an update view and a filtered list. You would do this when the portal needs pages for a sample type beyond the ones FairDM provides.

## Before you start

You need a form built on `SampleFormMixin` and a filter set built on `SampleFilterMixin` for a sample type. This guide uses `CoreSampleForm` and `CoreSampleFilter` for `CoreSample`, a sample type of your portal. To write them, see [How to customise a sample form](customise-a-sample-form.md) and [How to add a filter to a sample type](add-a-filter-to-a-sample-type.md).

## Steps

1. Write the create view. Pass the request to the form, because the form uses it to decide which datasets the person may choose.

   ```python
   from django.contrib.auth.mixins import LoginRequiredMixin

   from fairdm.views import FairDMCreateView
   from myportal.forms import CoreSampleForm
   from myportal.models import CoreSample


   class CoreSampleCreateView(LoginRequiredMixin, FairDMCreateView):
       model = CoreSample
       form_class = CoreSampleForm

       def get_form_kwargs(self):
           kwargs = super().get_form_kwargs()
           kwargs["request"] = self.request
           return kwargs
   ```

   After a save the view redirects to the sample's own page.

2. Write the update view in the same way.

   ```python
   from fairdm.views import FairDMUpdateView


   class CoreSampleUpdateView(LoginRequiredMixin, FairDMUpdateView):
       model = CoreSample
       form_class = CoreSampleForm

       def get_form_kwargs(self):
           kwargs = super().get_form_kwargs()
           kwargs["request"] = self.request
           return kwargs
   ```

   For a saved sample, the form leaves out `dataset` unless the person can manage the sample, so an editor cannot move it.

3. To edit the sample's identifiers or dates on the same page, list the row sets FairDM ships on the view.

   ```python
   from fairdm.core.related_records import SampleIdentifierInline


   class CoreSampleUpdateView(LoginRequiredMixin, FairDMUpdateView):
       model = CoreSample
       form_class = CoreSampleForm
       inlines = [SampleIdentifierInline]
   ```

   The view saves the sample and its rows together. `SampleDateInline` is the row set for dates.

4. Write the list view. Give it the filter set, and list only the samples the visitor may see.

   ```python
   from fairdm.views import FairDMListView
   from myportal.filters import CoreSampleFilter


   class CoreSampleListView(FairDMListView):
       model = CoreSample
       filterset_class = CoreSampleFilter
       list_item_template = "myportal/core_sample_card.html"

       def get_queryset(self):
           return (
               super()
               .get_queryset()
               .visible_to(self.request.user)
               .select_related("dataset")
           )
   ```

   The view builds the filter set with the request, so record filters offer what the visitor may see.

5. Write the card each row is drawn as. The list passes each sample to the template as `object`, and FairDM provides a Cotton component that draws a sample of any type. Save this as `myportal/templates/myportal/core_sample_card.html`.

   ```django
   <c-sample.card :object="object" />
   ```

   The component expects the sample's dataset to be loaded, which the `select_related` in step 4 does.

6. Add the views to your URLs.

   ```python
   from django.urls import path

   from myportal import views

   urlpatterns = [
       path("core-samples/", views.CoreSampleListView.as_view(), name="core-sample-list"),
       path("core-samples/add/", views.CoreSampleCreateView.as_view(), name="core-sample-add"),
       path("core-samples/<int:pk>/edit/", views.CoreSampleUpdateView.as_view(), name="core-sample-edit"),
   ]
   ```

## The result

The create and update pages draw the form in the page layout, through the form's crispy-forms helper, with a searchable dataset field and the location input. The list page shows a card for each sample, a search and sort when the filter set declares them, and the filter panel. See [Base views](../reference/base-views.md) for the view classes and [How to add search and sort to a list view](add-search-and-sort-to-a-list-view.md) for the toolbar.

The registry already builds the listing and edit pages of a registered type. Write views of your own only for pages the registry does not provide.
