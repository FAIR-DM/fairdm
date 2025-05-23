from crispy_forms.helper import FormHelper
from django import forms

from .models import Sample


class SampleForm(forms.ModelForm):
    class Meta:
        model = Sample
        exclude = ["created", "modified", "keywords", "depth", "options", "path", "numchild", "tags"]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)
        # if self.request:
        # self.fields["dataset"].queryset = self.request.user.datasets.all()
        # self.fields["dataset"].initial = self.request.GET.get("dataset")

        self.helper = FormHelper()
        self.helper.form_tag = False
        # self.helper.layout = convert_to_crispy_layout(fieldsets)

    # def save(self, commit=True):
    #     instance = super().save(commit=False)
    #     if commit:
    #         instance.save()
    #     return instance
