from django.contrib.auth.decorators import login_required
from django.db.models import Count, Max
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST

from apps.accounts.access import matter_access_required
from apps.contacts.functions.load_contacts import load_contacts
from apps.contacts.models import Contact
from apps.management.selection import (
    all_visible_selected,
    clear_selected_ids,
    get_selected_ids,
    get_session_key,
    select_all_ids,
    selection_response,
    toggle_id,
)
from apps.matters.contacts.filters import MatterContactFilter
from apps.matters.models import Group, Matter, Relationship, Role

DEFAULT_MATTER_CONTACT_FILTER = {"order_by": "group"}

# HX-Trigger that refreshes the #contacts panel.
CONTACTS_TRIGGER = "contactsReload"


def _selection_key(matter):
    return get_session_key("selected_matter_contacts", matter.id)


def _filtered_relationships(request, matter):
    """The matter's party relationships with the current session filter/sort applied."""
    filter_data = (
        request.session.get(f"matter_contacts_filter_{matter.id}", {})
        or DEFAULT_MATTER_CONTACT_FILTER
    )
    return MatterContactFilter(
        filter_data, queryset=load_contacts(matter), matter=matter
    ).qs


def get_contact_list(request, matter):
    """Build the contact list with filtering and sorting applied."""
    session_key = f"matter_contacts_filter_{matter.id}"
    filter_data = request.session.get(session_key, {})

    contacts_qs = _filtered_relationships(request, matter)

    # Build unified list with matter.client as first row if exists
    contact_list = []

    if matter.client:
        # Only include client row if not filtering by non-Client group
        group_filter = filter_data.get("group", "")
        if isinstance(group_filter, list):
            group_filter = group_filter[0] if group_filter else ""
        # Check if filtering by Client group (ID) or no filter
        client_group = Group.objects.filter(matter__isnull=True, name="Client").first()
        if not group_filter or str(group_filter) == str(
            client_group.id if client_group else ""
        ):
            contact_list.append(
                {
                    "group": "Client",
                    "role_name": "Client",
                    "contact": matter.client,
                    "relationship_id": None,
                    "is_client": True,
                }
            )

    for rel in contacts_qs:
        contact_list.append(
            {
                "group": rel.group.name,
                "role_name": rel.role.name,
                "contact": rel.contact,
                "relationship_id": rel.id,
                "is_client": False,
            }
        )

    current_order = filter_data.get("order_by", "group") if filter_data else "group"
    if isinstance(current_order, list):
        current_order = current_order[0] if current_order else "group"

    # Add band index for visual grouping when sorted by group
    order_field = current_order.lstrip("-")
    if order_field == "group":
        current_group = None
        band = 0
        for item in contact_list:
            if item["group"] != current_group:
                current_group = item["group"]
                band = 1 - band
            item["band"] = band

    # Get current filter values for dropdown display
    group_id = filter_data.get("group", "")
    if isinstance(group_id, list):
        group_id = group_id[0] if group_id else ""
    role_id = filter_data.get("role", "")
    if isinstance(role_id, list):
        role_id = role_id[0] if role_id else ""

    # Get selected names for display
    selected_group = None
    selected_role = None
    if group_id:
        group_obj = Group.objects.filter(id=group_id).first()
        selected_group = group_obj.name if group_obj else None
    if role_id:
        role_obj = Role.objects.filter(id=role_id).first()
        selected_role = role_obj.name if role_obj else None

    # Multi-select state (the synthetic client row has no relationship, so it's
    # never selectable).
    selected_ids = get_selected_ids(request, _selection_key(matter))
    visible_ids = [i["relationship_id"] for i in contact_list if i["relationship_id"]]

    return {
        "contacts": contact_list,
        "current_order": order_field,
        "session_key": session_key,
        "groups": Group.objects.for_matter(matter),
        "roles": Role.objects.filter(is_active=True).order_by("name"),
        "group_id": int(group_id) if group_id else None,
        "role_id": int(role_id) if role_id else None,
        "selected_group": selected_group,
        "selected_role": selected_role,
        "selected_ids": selected_ids,
        "all_selected": all_visible_selected(selected_ids, visible_ids),
    }


@login_required
@matter_access_required
def index(request, id):
    matter = get_object_or_404(Matter, pk=id)

    contact_data = get_contact_list(request, matter)

    context = {
        "app": "matters",
        "subapp": "contacts",
        "matter": matter,
        **contact_data,
    }

    return render(request, "matters/contacts/list.html", context)


@login_required
@matter_access_required
def contact_list(request, id):
    """HTMX endpoint to reload the contact table."""
    matter = get_object_or_404(Matter, pk=id)

    contact_data = get_contact_list(request, matter)

    context = {
        "matter": matter,
        **contact_data,
    }

    return render(request, "matters/contacts/contact-table.html", context)


@login_required
@matter_access_required
def contact_filter(request, id):
    """Handle filter form display and submission."""
    matter = get_object_or_404(Matter, pk=id)
    session_key = f"matter_contacts_filter_{matter.id}"

    if request.method == "POST":
        request.session[session_key] = request.POST
        return HttpResponse(status=204, headers={"HX-Trigger": "contactsReload"})

    filter_data = request.session.get(session_key, {})
    contacts_qs = load_contacts(matter)
    filter_form = MatterContactFilter(filter_data, queryset=contacts_qs, matter=matter)

    context = {
        "filter": filter_form,
        "matter": matter,
        "session_key": session_key,
    }

    return render(request, "matters/contacts/filter.html", context)


@login_required
@matter_access_required
def contact_sort(request, id, order):
    """Handle column sorting."""
    matter = get_object_or_404(Matter, pk=id)
    session_key = f"matter_contacts_filter_{matter.id}"
    filter_data = dict(request.session.get(session_key, {}))

    current_order = filter_data.get("order_by", "")
    if isinstance(current_order, list):
        current_order = current_order[0] if current_order else ""

    if current_order == order:
        new_order = f"-{order}" if not current_order.startswith("-") else order
    else:
        new_order = order

    filter_data["order_by"] = new_order
    request.session[session_key] = filter_data

    return HttpResponse(status=204, headers={"HX-Trigger": "contactsReload"})


@login_required
@matter_access_required
def assign(request, id):
    matter = get_object_or_404(Matter, pk=id)
    groups = Group.objects.for_matter(matter)
    roles = (
        Role.objects.filter(is_active=True)
        .exclude(is_system=True)
        .exclude(name="Client (Invoicing)")
        .order_by("name")
    )

    context = {
        "matter": matter,
        "groups": groups,
        "roles": roles,
    }

    return render(request, "matters/contacts/assign-modal.html", context)


@login_required
@matter_access_required
def assign_results(request, id):
    matter = get_object_or_404(Matter, pk=id)
    text = request.POST.get("search_text")

    if text:
        contacts = Contact.objects.filter(name__icontains=text).order_by("name")
    else:
        contacts = None

    context = {
        "matter": matter,
        "contacts": contacts,
    }

    return render(request, "matters/contacts/results.html", context)


@login_required
def assign_store(request):
    matter = get_object_or_404(Matter, pk=request.POST["matter_id"])
    contact = get_object_or_404(Contact, pk=request.POST["contact_id"])
    group = get_object_or_404(Group, pk=request.POST["group_id"])
    role = get_object_or_404(Role, pk=request.POST["role_id"])

    Relationship.objects.create(matter=matter, contact=contact, group=group, role=role)

    return HttpResponse(status=204, headers={"HX-Trigger": "contactsReload"})


@login_required
def assign_edit(request, id):
    relationship = get_object_or_404(Relationship, pk=id)
    matter = get_object_or_404(Matter, pk=relationship.matter_id)
    contact = get_object_or_404(Contact, pk=relationship.contact_id)
    groups = Group.objects.for_matter(matter)
    roles = (
        Role.objects.filter(is_active=True)
        .exclude(is_system=True)
        .exclude(name="Client (Invoicing)")
        .order_by("name")
    )

    context = {
        "matter": matter,
        "contact": contact,
        "relationship": relationship,
        "groups": groups,
        "roles": roles,
    }

    return render(request, "matters/contacts/assign-role-modal.html", context)


@login_required
def assign_update(request, id):
    relationship = get_object_or_404(Relationship, pk=id)
    relationship.group_id = request.POST.get("group_id")
    relationship.role_id = request.POST.get("role_id")
    relationship.save()
    return HttpResponse(status=204, headers={"HX-Trigger": "contactsReload"})


@login_required
def assign_delete(request, id):
    relationship = get_object_or_404(Relationship, pk=id)
    relationship.delete()
    return HttpResponse(status=204, headers={"HX-Trigger": "contactsReload"})


@login_required
@matter_access_required
def filter_group(request, id, group_id):
    """Quick filter by group from dropdown."""
    session_key = f"matter_contacts_filter_{id}"
    filter_data = dict(request.session.get(session_key, {}))
    filter_data["group"] = "" if group_id == 0 else group_id
    request.session[session_key] = filter_data
    return HttpResponse(status=204, headers={"HX-Trigger": "contactsReload"})


@login_required
@matter_access_required
def filter_role(request, id, role_id):
    """Quick filter by role from dropdown."""
    session_key = f"matter_contacts_filter_{id}"
    filter_data = dict(request.session.get(session_key, {}))
    filter_data["role"] = "" if role_id == 0 else role_id
    request.session[session_key] = filter_data
    return HttpResponse(status=204, headers={"HX-Trigger": "contactsReload"})


# --- Matter-specific groups (Group rows scoped to one matter) ----------------


def _group_context(matter, editing_id=None):
    groups = matter.groups.annotate(party_count=Count("relationship")).order_by(
        "order", "name"
    )
    return {"matter": matter, "groups": groups, "editing_id": editing_id}


@login_required
@matter_access_required
def group_manage(request, id):
    """Modal to add/rename/remove groups scoped to this matter."""
    matter = get_object_or_404(Matter, pk=id)
    return render(request, "matters/contacts/group-modal.html", _group_context(matter))


@login_required
@matter_access_required
def group_list(request, id):
    """The list partial on its own — used to toggle a row into rename mode
    (?edit=<pk>) and to cancel back out of it."""
    matter = get_object_or_404(Matter, pk=id)
    editing = request.GET.get("edit")
    editing_id = int(editing) if editing and editing.isdigit() else None
    return render(
        request,
        "matters/contacts/group-list.html",
        _group_context(matter, editing_id),
    )


@login_required
@matter_access_required
def group_add(request, id):
    matter = get_object_or_404(Matter, pk=id)
    name = (request.POST.get("name") or "").strip()
    if name:
        # Number matter groups from the matter-group band up so they always sort
        # after the firm-wide groups (see Group.MATTER_GROUP_ORDER_BASE).
        max_order = (
            matter.groups.aggregate(Max("order"))["order__max"]
            or Group.MATTER_GROUP_ORDER_BASE
        )
        Group.objects.create(matter=matter, name=name, order=max_order + 1)
    response = render(
        request, "matters/contacts/group-list.html", _group_context(matter)
    )
    response.headers["HX-Trigger"] = "contactsReload"
    return response


@login_required
@matter_access_required
def group_edit(request, id, group_pk):
    matter = get_object_or_404(Matter, pk=id)
    name = (request.POST.get("name") or "").strip()
    # Scoped to this matter so a global group can't be renamed from here.
    group = Group.objects.filter(pk=group_pk, matter=matter).first()
    if group and name:
        group.name = name
        group.save()
    response = render(
        request, "matters/contacts/group-list.html", _group_context(matter)
    )
    response.headers["HX-Trigger"] = "contactsReload"
    return response


@login_required
@matter_access_required
def group_delete(request, id, group_pk):
    matter = get_object_or_404(Matter, pk=id)
    # Scoped to this matter so a global group can't be deleted from here.
    Group.objects.filter(pk=group_pk, matter=matter).delete()
    response = render(
        request, "matters/contacts/group-list.html", _group_context(matter)
    )
    response.headers["HX-Trigger"] = "contactsReload"
    return response


# --- Multi-select bulk actions on the parties list ---------------------------


@login_required
@matter_access_required
@require_POST
def toggle_select(request, id, relationship_id):
    """Toggle one party in the selection."""
    matter = get_object_or_404(Matter, pk=id)
    toggle_id(request, _selection_key(matter), relationship_id)
    return selection_response(CONTACTS_TRIGGER)


@login_required
@matter_access_required
@require_POST
def select_all(request, id):
    """Select/deselect every party currently visible under the active filter."""
    matter = get_object_or_404(Matter, pk=id)
    visible_ids = list(
        _filtered_relationships(request, matter).values_list("id", flat=True)
    )
    select_all_ids(request, _selection_key(matter), visible_ids)
    return selection_response(CONTACTS_TRIGGER)


@login_required
@matter_access_required
@require_POST
def clear_selection(request, id):
    matter = get_object_or_404(Matter, pk=id)
    clear_selected_ids(request, _selection_key(matter))
    return selection_response(CONTACTS_TRIGGER)


@login_required
@matter_access_required
@require_POST
def bulk_group(request, id):
    """Move the selected parties into one group. Selection is kept so a role
    change can follow."""
    matter = get_object_or_404(Matter, pk=id)
    selected = get_selected_ids(request, _selection_key(matter))
    group = (
        Group.objects.for_matter(matter).filter(pk=request.POST.get("group_id")).first()
    )
    if selected and group:
        Relationship.objects.filter(matter=matter, id__in=selected).update(group=group)
    return selection_response(CONTACTS_TRIGGER)


@login_required
@matter_access_required
@require_POST
def bulk_role(request, id):
    """Set the role on the selected parties. Selection is kept."""
    matter = get_object_or_404(Matter, pk=id)
    selected = get_selected_ids(request, _selection_key(matter))
    role = Role.objects.filter(is_active=True, pk=request.POST.get("role_id")).first()
    if selected and role:
        Relationship.objects.filter(matter=matter, id__in=selected).update(role=role)
    return selection_response(CONTACTS_TRIGGER)


@login_required
@matter_access_required
@require_POST
def bulk_remove(request, id):
    """Remove the selected parties from the matter, then clear the selection."""
    matter = get_object_or_404(Matter, pk=id)
    key = _selection_key(matter)
    selected = get_selected_ids(request, key)
    if selected:
        Relationship.objects.filter(matter=matter, id__in=selected).delete()
    clear_selected_ids(request, key)
    return selection_response(CONTACTS_TRIGGER)
