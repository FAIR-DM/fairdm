"""SKETCH ONLY. Stand-in create pages, so the dataset and sample fields can be seen.

The portal has no create page for samples or measurements yet (R16). These show the registered
types' own forms, limited to the fields this feature changes. Nothing is saved.
"""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from mvp.views import MVPFormView

from fairdm.registry import registry


def _registered(kind, model_name):
    models = registry.samples if kind == "sample" else registry.measurements
    return next(m for m in models if m._meta.model_name == model_name)


class SketchCreatePage(MVPFormView):
    template_name = "form_view.html"
    kind = "sample"
    model_name = "rocksample"
    fields = ("name", "dataset")
    page_title = _("New sample")

    def get_form_class(self):
        from django import forms

        from fairdm.core.measurement.forms import MeasurementFormMixin
        from fairdm.core.sample.forms import SampleFormMixin

        mixin = SampleFormMixin if self.kind == "sample" else MeasurementFormMixin
        model = _registered(self.kind, self.model_name)
        return type(
            "SketchForm",
            (mixin, forms.ModelForm),
            {"Meta": type("Meta", (), {"model": model, "fields": list(self.fields)})},
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_page_title(self):
        return self.page_title

    def form_valid(self, form):
        messages.info(self.request, _("The form is valid. Nothing was saved: this is a sketch."))
        return self.render_to_response(self.get_context_data(form=form))


class SketchNewSample(SketchCreatePage):
    pass


class SketchNewMeasurement(SketchCreatePage):
    kind = "measurement"
    model_name = "xrfmeasurement"
    fields = ("name", "dataset", "sample")
    page_title = _("New measurement")
