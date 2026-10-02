"""The message, report and resolve forms."""

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage, ProblemReport


class ContactForm(forms.ModelForm):
    """What a message is about, and the message. The message is sent and never saved."""

    message = forms.CharField(
        label=_("Your message"),
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 8}),
        help_text=_("Plain text, up to 2,000 characters."),
    )

    class Meta:
        model = ContactMessage
        fields = ["subject"]
        labels = {"subject": _("What is your message about?")}
        widgets = {"subject": forms.RadioSelect}

    def __init__(self, *args, subjects=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].help_text = ""
        if subjects:
            self.fields["subject"].choices = subjects
        else:
            # A person or an organization has no data or specimen to ask for.
            del self.fields["subject"]


class ReportForm(forms.ModelForm):
    """A description of the problem."""

    class Meta:
        model = ProblemReport
        fields = ["description"]
        labels = {"description": _("What is wrong?")}
        widgets = {"description": forms.Textarea(attrs={"rows": 8})}
        help_texts = {
            "description": _(
                "Say which value or field, what it shows and what you expected. "
                "Plain text, up to 2,000 characters."
            )
        }


class ResolveForm(forms.ModelForm):
    """The note a resolver may leave for the reader who reported the problem."""

    class Meta:
        model = ProblemReport
        fields = ["note"]
