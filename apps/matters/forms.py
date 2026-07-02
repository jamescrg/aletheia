from django import forms

from apps.contacts.models import Contact
from config.settings import CustomFormRendererCompact

from .models import Matter, PracticeArea


class ContactComboboxWidget(forms.Widget):
    """Typeahead combobox for choosing a contact. Renders a search input plus a
    hidden value input that carries the field's value on submit. Reuses
    static/js/combobox.js and the contact-search results partial
    (templates/matters/contacts/results.html, served by matters:client-search)."""

    template_name = "matters/widgets/contact_combobox.html"

    def id_for_label(self, id_):
        # The label points at the visible search input (the id combobox.js binds
        # to), not the hidden value input.
        return "assign-search-input"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        selected_name = ""
        if value not in (None, ""):
            contact = Contact.objects.filter(pk=value).first()
            selected_name = contact.name if contact else ""
        context["widget"]["selected_name"] = selected_name
        return context


class MatterForm(forms.ModelForm):
    class Meta:
        model = Matter

        fields = (
            "client",
            "status",
            "date_start",
            "name",
            "practice_area",
            "description",
            "work_status",
            "jurisdiction",
            "billable",
            "billing_type",
            "deferred_fees",
            "flat_fee_amount",
        )

        STATUSES = (
            ("Pending", "Pending"),
            ("Open", "Open"),
            ("Complete", "Complete"),
            ("Closed", "Closed"),
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "onfocus": "moveFocusToEnd(this)",
                    "class": "span2",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "span3",
                }
            ),
            "work_status": forms.TextInput(
                attrs={
                    "class": "span2",
                }
            ),
            "status": forms.Select(
                choices=STATUSES,
            ),
            "client": ContactComboboxWidget(),
            "date_start": forms.DateInput(attrs={"type": "date"}),
            "jurisdiction": forms.TextInput(),
            "billable": forms.Select(
                choices=((True, "Yes"), (False, "No (Administrative)")),
            ),
            "billing_type": forms.Select(
                attrs={"onchange": "toggleFlatFeeAmount()"},
            ),
            "flat_fee_amount": forms.NumberInput(
                attrs={"step": "0.01"},
            ),
            "deferred_fees": forms.Select(
                choices=((False, "No"), (True, "Yes")),
            ),
        }

        labels = {
            "name": "Matter Name",
            "date_start": "Open Date",
            "clio_matter_id": "Clio Matter",
            "client_reference_id": "Client Reference",
            "practice_area": "Practice Area",
            "billing_type": "Billing Type",
            "flat_fee_amount": "Flat Fee Amount",
            "deferred_fees": "Deferred Fee Arrangement",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()

        # client is nullable on the model but not blank, so the form would force
        # it; relax it here so administrative matters with no client can save.
        # (name/description/work_status get their optionality from the model.)
        self.fields["client"].required = False

        # Any contact can be a matter's client (the typeahead searches all
        # contacts), so validate the submitted pk against the full set.
        self.fields["client"].queryset = Contact.objects.all()

        # Validate server-side (as the add view already does) rather than via
        # the HTML5 `required` attribute. Otherwise the browser silently refuses
        # to submit the edit modal when a required field is empty or not
        # focusable, with no error shown to the user.
        self.use_required_attribute = False

        # Filter practice areas to only show active ones
        self.fields["practice_area"].queryset = PracticeArea.objects.filter(
            is_active=True
        )
