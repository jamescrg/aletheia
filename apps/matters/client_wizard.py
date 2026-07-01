"""In-form contact creation for the matter client picker.

From the client combobox on the add-matter form, the user can create a new
contact — or convert an intake — without losing their in-progress matter. Because
the app has a single modal container (a swap into it destroys the matter form),
this runs as an in-place wizard that swaps only the ``.modal-dialog`` and stashes
the matter form's current field values in the session, restoring them when the
matter form is re-rendered with the newly chosen client selected.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.contacts.forms import ContactForm
from apps.folders.models import Folder
from apps.intakes.models import Intake
from apps.matters.forms import MatterForm

# Everything the launching button POSTs from the matter form except the CSRF
# token and the combobox's own search box.
_SKIP = {"csrfmiddlewaretoken", "search_text"}


def _stash_matter_draft(request):
    request.session["matter_client_draft"] = {
        k: v for k, v in request.POST.items() if k not in _SKIP
    }
    request.session.modified = True


def _folder_qs():
    return Folder.objects.filter(app="contacts").order_by("name")


def _contact_context(form, intake_id=None):
    """Context for the contact form when rendered inside the wizard: it submits
    back to the matter form and its Cancel becomes a Back button."""
    return {
        "app": "contacts",
        "edit": False,
        "add": True,
        "action": reverse("matters:client-create-contact"),
        "form": form,
        "intake_id": intake_id,
        "matter_return": True,
        "modal_target": "#htmx-modal-container .modal-dialog",
        "modal_swap": "outerHTML",
    }


def _render_matter_dialog(request, client_id=None):
    """Re-render the matter form from the stashed draft (consuming it),
    optionally with a freshly-created client selected."""
    draft = dict(request.session.pop("matter_client_draft", {}))
    request.session.modified = True
    if client_id is not None:
        draft["client"] = str(client_id)
    form = MatterForm(initial=draft, use_required_attribute=False)
    context = {
        "app": "matters",
        "edit": False,
        "add": True,
        "action": "/matters/add",
        "form": form,
    }
    return render(request, "matters/form.html", context)


@login_required
def client_new_contact(request):
    """ "+ Create new contact": stash the matter draft, open the contact form
    (name prefilled from the combobox search text)."""
    _stash_matter_draft(request)
    search_text = (request.POST.get("search_text") or "").strip()
    form = ContactForm(
        initial={"name": search_text} if search_text else None,
        use_required_attribute=False,
    )
    form.fields["folder"].queryset = _folder_qs()
    return render(request, "contacts/form.html", _contact_context(form))


@login_required
def client_intake_picker(request):
    """ "+ Convert an intake": stash the matter draft, list unconverted intakes."""
    _stash_matter_draft(request)
    intakes = Intake.objects.filter(contact__isnull=True).order_by("-date")
    return render(request, "matters/client-intake-picker.html", {"intakes": intakes})


@login_required
def client_intake_contact(request, id):
    """An intake was picked: open the contact form prefilled from it (the draft
    is already stashed from the picker step)."""
    intake = get_object_or_404(Intake, pk=id)
    form = ContactForm(
        initial={
            "name": intake.name,
            "address": intake.address,
            "phone1": intake.phone,
            "phone1_label": "Mobile",
            "email": intake.email,
        },
        use_required_attribute=False,
    )
    form.fields["folder"].queryset = _folder_qs()
    return render(request, "contacts/form.html", _contact_context(form, intake_id=id))


@login_required
def client_create_contact(request):
    """Save the new contact, then return to the matter form with it selected."""
    form = ContactForm(request.POST, use_required_attribute=False)
    if form.is_valid():
        contact = form.save(commit=False)
        contact.user = request.user
        intake_id = request.POST.get("intake_id")
        if intake_id:
            contact.intake = get_object_or_404(Intake, pk=intake_id)
        contact.save()
        return _render_matter_dialog(request, client_id=contact.id)
    # Validation error — re-render the contact form in the dialog.
    form.fields["folder"].queryset = _folder_qs()
    return render(
        request,
        "contacts/form.html",
        _contact_context(form, intake_id=request.POST.get("intake_id")),
    )


@login_required
def client_cancel(request):
    """Back out of the sub-flow: re-render the matter form from the draft."""
    return _render_matter_dialog(request)
