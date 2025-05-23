from fairdm.views import BaseCRUDView

from ..forms import SampleForm
from ..models import Sample
from ..utils import model_class_inheritance_to_fieldsets


class SampleCRUDView(BaseCRUDView):
    url_base = "sample"
    form_class = SampleForm
    template_name = "sample/sample_detail.html"
    # @property
    # def model(self):
    #     if sample_type := self.request.GET.get("type"):
    #         return apps.get_model(sample_type)
    #     return Sample

    def get_object(self):
        sample = Sample.objects.get(uuid=self.kwargs["uuid"])
        self.model = type(sample)
        return sample

    def get_detail_context_data(self, context):
        context["descriptions"] = self.get_object().descriptions.all()
        context["all_types"] = self.object.DESCRIPTION_TYPES.choices
        context["model_config"] = self.model.config
        return context

    def get_form_class(self):
        return self.model.config.get_form_class()

    def get_form(self, data=None, files=None, **kwargs):
        kwargs["request"] = self.request
        if data:
            data = data.copy()
            data["type"] = self.model._meta.label
            data["_position"] = "first-child"
            data["dataset"] = self.request.GET.get("dataset")
        return super().get_form(data, files, **kwargs)

    def get_sidebar_fields(self):
        return model_class_inheritance_to_fieldsets(self.object)
