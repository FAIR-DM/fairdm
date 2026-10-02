"""The Contact and Report a problem pages, and the list of a record's reported problems.

Prototype code for specification 027. Specification 021 (#401) will let a plugin declare itself a
page action. Until it does, these are registered as ordinary plugins kept out of the tab strip, and
``templatetags/contact.py`` stands in for the dropdown.
"""

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.core.mail import EmailMessage
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from django.views.generic import View
from mvp.views import MVPFormView

from fairdm import plugins
from fairdm.contrib.contributors.models import Contributor
from fairdm.contrib.plugins import Plugin, reverse
from fairdm.core.dataset.models import Dataset
from fairdm.core.measurement.models import Measurement
from fairdm.core.project.models import Project
from fairdm.core.sample.models import Sample
from fairdm.views import FairDMTemplateView

from . import rules
from .forms import ContactForm, ReportForm, ResolveForm
from .models import ContactMessage, ProblemReport


def record_url(request, obj):
    """Return the record's address in full, for an email."""
    return request.build_absolute_uri(obj.get_absolute_url())


def send(request, template, context, recipients, reply_to=None):
    """Send one plain-text email to each recipient, so none sees another's address."""
    body = render_to_string(f"contact/email/{template}.txt", context, request=request)
    subject, _separator, text = body.partition("\n")
    for person in recipients:
        EmailMessage(
            subject=subject.strip(),
            body=text.strip(),
            to=[person.email],
            reply_to=[reply_to] if reply_to else None,
        ).send()


class SenderMixin:
    """What the two sending pages share: sign-in first, a verified address, and the daily limit."""

    slug_field = "pk"
    template_name = "contact/send.html"

    def dispatch(self, request, *args, **kwargs):
        """Send a signed-out visitor to sign in, then bring them back to this page."""
        if not request.user.is_authenticated:
            if not rules.is_visible(request.user, self.base_object):
                raise Http404
            return redirect_to_login(request.get_full_path())
        return super().dispatch(request, *args, **kwargs)

    def handle_no_permission(self):
        """Answer as for a record that does not exist."""
        raise Http404

    def get_blocked(self):
        """Return why the visitor cannot send, or an empty string when they can."""
        if not rules.email_is_verified(self.request.user):
            return "unverified"
        if rules.at_limit(self.request.user):
            return "limit"
        return ""

    def get_context_data(self, **kwargs):
        """Add the record, why sending is blocked, and where Cancel leads."""
        context = super().get_context_data(**kwargs)
        context["record"] = self.base_object
        context["blocked"] = self.get_blocked()
        context["daily_limit"] = rules.daily_limit()
        context["back_url"] = self.base_object.get_absolute_url()
        context["kind"] = self.base_object._meta.verbose_name
        if isinstance(self.base_object, Contributor):
            context["kind"] = (
                gettext("organization")
                if self.base_object.is_organization
                else gettext("person")
            )
        return context

    def post(self, request, *args, **kwargs):
        """Refuse a sender who is blocked, whatever they posted."""
        if self.get_blocked():
            return self.get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        """Return to the record."""
        return self.base_object.get_absolute_url()

    def get_success_message(self, cleaned_data):
        """The confirmation is added by ``form_valid``."""
        return ""


def can_be_contacted(request, obj):
    """Open the Contact page only for a record the visitor may open and that someone can answer for."""
    if obj is None:
        return True
    if not rules.is_visible(request.user, obj):
        return False
    recipients, _rule = rules.contact_recipients(obj, request.user)
    return bool(recipients)


@plugins.register(
    Project, Dataset, Contributor, label=_("Contact"), icon="email", menu=False
)
class Contact(SenderMixin, Plugin, MVPFormView):
    """Write to a record's team, a person, or an organization's owner and administrators."""

    name = "contact"
    check = staticmethod(can_be_contacted)
    model = ContactMessage
    form_class = ContactForm
    page_title = _("Contact")

    def get_subjects(self):
        """Offer the two requests only where there is data or a specimen to ask for."""
        if isinstance(self.base_object, Contributor):
            return None
        return ContactMessage.Subject.choices

    def get_form_kwargs(self):
        """Pass the subjects this page offers."""
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        kwargs["subjects"] = self.get_subjects()
        return kwargs

    def get_initial(self):
        """Start on a general question."""
        return {"subject": ContactMessage.Subject.QUESTION}

    def get_context_data(self, **kwargs):
        """Add who the message goes to."""
        context = super().get_context_data(**kwargs)
        recipients, rule = rules.contact_recipients(self.base_object, self.request.user)
        context.update(
            {"mode": "contact", "recipients": recipients, "recipient_rule": rule}
        )
        return context

    def form_valid(self, form):
        """Send the message, keep a record that it was sent, and return to the record."""
        obj = self.base_object
        recipients, _rule = rules.contact_recipients(obj, self.request.user)
        subject = form.cleaned_data.get("subject", ContactMessage.Subject.QUESTION)
        sent = ContactMessage.objects.create(
            sender=self.request.user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            subject=subject,
        )
        send(
            self.request,
            "contact",
            {
                "sender": self.request.user,
                "sender_url": self.request.build_absolute_uri(
                    self.request.user.get_absolute_url()
                ),
                "record": obj,
                "record_url": record_url(self.request, obj),
                "subject": sent.get_subject_display(),
                "message": form.cleaned_data["message"],
            },
            recipients,
            reply_to=self.request.user.email,
        )
        messages.success(
            self.request,
            gettext("Your message was sent. A reply will come to your email address."),
        )
        return redirect(self.get_success_url())


def can_be_reported(request, obj):
    """Open the report page for any record the visitor may open."""
    return obj is None or rules.is_visible(request.user, obj)


@plugins.register(
    Dataset,
    Sample,
    Measurement,
    label=_("Report a problem"),
    icon="warning",
    menu=False,
)
class ReportProblem(SenderMixin, Plugin, MVPFormView):
    """Describe something wrong with a dataset, sample or measurement."""

    name = "report-problem"
    check = staticmethod(can_be_reported)
    model = ProblemReport
    form_class = ReportForm
    page_title = _("Report a problem")

    def get_form_kwargs(self):
        """A report is always new."""
        kwargs = super().get_form_kwargs()
        kwargs.pop("instance", None)
        return kwargs

    def get_context_data(self, **kwargs):
        """Say which screen this is."""
        context = super().get_context_data(**kwargs)
        context["mode"] = "report"
        return context

    def form_valid(self, form):
        """Record the report, tell the people who can fix it, and return to the record."""
        obj = self.base_object
        report = form.save(commit=False)
        report.reporter = self.request.user
        report.content_type = ContentType.objects.get_for_model(obj)
        report.object_id = obj.pk
        report.dataset = rules.dataset_of(obj)
        report.save()
        send(
            self.request,
            "report",
            {
                "reporter": self.request.user,
                "record": obj,
                "record_url": record_url(self.request, obj),
                "list_url": self.request.build_absolute_uri(
                    reverse(obj, "reported-problems")
                ),
                "description": report.description,
            },
            rules.report_recipients(obj),
        )
        messages.success(
            self.request,
            gettext(
                "Thank you. Your report was received, and you'll get an email when it is resolved."
            ),
        )
        return redirect(self.get_success_url())


def may_see_reports(request, obj):
    """Open the list only for someone who may edit the record."""
    return obj is None or rules.may_edit(request.user, obj)


class ReportTransition(Plugin, View):
    """Mark a report resolved, or reopen it."""

    url_path = "<int:pk>/<str:action>"
    name = "transition"
    http_method_names = ["post"]

    def handle_no_permission(self):
        """Answer as for a record that does not exist."""
        raise Http404

    def post(self, request, *args, **kwargs):
        """Change the report's state and return to the list it was on."""
        obj = self.base_object
        report = get_object_or_404(rules.reports_for(obj), pk=kwargs["pk"])
        if kwargs["action"] == "resolve":
            form = ResolveForm(request.POST, instance=report)
            report = form.save(commit=False)
            report.state = ProblemReport.State.RESOLVED
            report.resolved_by = request.user
            report.resolved = timezone.now()
            report.save()
            send(
                request,
                "resolved",
                {
                    "report": report,
                    "record": report.record,
                    "record_url": record_url(request, report.record),
                },
                rules.active([report.reporter]),
            )
            messages.success(
                request,
                gettext(
                    "Marked as resolved. The person who reported it has been told."
                ),
            )
        else:
            report.state = ProblemReport.State.OPEN
            report.resolved_by = None
            report.resolved = None
            report.save()
            messages.success(request, gettext("Reopened."))
        target = reverse(obj, "reported-problems")
        if request.POST.get("show") == "resolved":
            target += "?show=resolved"
        return redirect(target)


@plugins.register(
    Dataset,
    Sample,
    Measurement,
    label=_("Reported problems"),
    icon="warning",
    menu=False,
)
class ReportedProblems(Plugin, FairDMTemplateView):
    """The problems readers have reported on a record, for the people who can fix them."""

    name = "reported-problems"
    check = staticmethod(may_see_reports)
    template_name = "contact/reported_problems.html"
    page_title = _("Reported problems")
    extra_views = [ReportTransition]

    def handle_no_permission(self):
        """Answer as for a page that does not exist, so nobody learns a record has reports."""
        raise Http404

    def get_rows(self, reports):
        """Name the kind of record each report is about, as the record's own type calls itself."""
        rows = []
        for report in reports:
            if report.record is None:
                continue
            report.kind = report.record._meta.verbose_name
            rows.append(report)
        return rows

    def get_context_data(self, **kwargs):
        """Add the open or the resolved reports, and how many there are of each."""
        context = super().get_context_data(**kwargs)
        obj = self.base_object
        reports = rules.reports_for(obj).select_related(
            "reporter", "resolved_by", "content_type"
        )
        show = "resolved" if self.request.GET.get("show") == "resolved" else "open"
        context.update(
            {
                "record": obj,
                "show": show,
                "reports": self.get_rows(reports.filter(state=show)),
                "open_count": reports.filter(state=ProblemReport.State.OPEN).count(),
                "resolved_count": reports.filter(
                    state=ProblemReport.State.RESOLVED
                ).count(),
                "is_dataset": isinstance(obj, Dataset),
                "list_url": reverse(obj, "reported-problems"),
                "back_url": obj.get_absolute_url(),
            }
        )
        return context
