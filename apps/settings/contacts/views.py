from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.http import HttpResponse
from django.shortcuts import render

from apps.matters.models import Group, Role
from apps.settings.contacts.forms import GroupForm, RoleForm


@login_required
def contacts_index(request):
    roles = Role.objects.all().order_by("name")
    groups = Group.objects.all().order_by("order")

    context = {
        "subapp": "contacts",
        "roles": roles,
        "groups": groups,
    }

    return render(request, "settings/contacts/index.html", context)


@login_required
def role_list(request):
    roles = Role.objects.all().order_by("name")

    context = {
        "roles": roles,
    }

    return render(request, "settings/contacts/role-table.html", context)


@login_required
def add_role(request):
    if request.method == "POST":
        form = RoleForm(request.POST)

        if form.is_valid():
            form.save()

            return HttpResponse(status=204, headers={"HX-Trigger": "roleListReload"})
    else:
        form = RoleForm()

    context = {
        "form": form,
    }

    return render(request, "settings/contacts/role-form.html", context)


@login_required
def edit_role(request, role_id):
    role = Role.objects.get(id=role_id)

    if request.method == "POST":
        form = RoleForm(request.POST, instance=role)

        if form.is_valid():
            form.save()

            return HttpResponse(status=204, headers={"HX-Trigger": "roleListReload"})
    else:
        form = RoleForm(instance=role)

    context = {
        "form": form,
        "role": role,
    }

    return render(request, "settings/contacts/role-form.html", context)


@login_required
def delete_role(request, role_id):
    try:
        Role.objects.get(id=role_id).delete()
        return HttpResponse(status=204, headers={"HX-Trigger": "roleListReload"})
    except ProtectedError:
        error_message = "Cannot delete role: it is in use by one or more relationships."
        trigger = f'{{"showToast": {{"message": "{error_message}", "type": "error"}}}}'
        return HttpResponse(status=200, headers={"HX-Trigger": trigger})


# Group views


@login_required
def group_list(request):
    groups = Group.objects.all().order_by("order")

    context = {
        "groups": groups,
    }

    return render(request, "settings/contacts/group-table.html", context)


@login_required
def add_group(request):
    if request.method == "POST":
        form = GroupForm(request.POST)

        if form.is_valid():
            form.save()

            return HttpResponse(status=204, headers={"HX-Trigger": "groupListReload"})
    else:
        form = GroupForm()

    context = {
        "form": form,
    }

    return render(request, "settings/contacts/group-form.html", context)


@login_required
def edit_group(request, group_id):
    group = Group.objects.get(id=group_id)

    if request.method == "POST":
        form = GroupForm(request.POST, instance=group)

        if form.is_valid():
            form.save()

            return HttpResponse(status=204, headers={"HX-Trigger": "groupListReload"})
    else:
        form = GroupForm(instance=group)

    context = {
        "form": form,
        "group": group,
    }

    return render(request, "settings/contacts/group-form.html", context)


@login_required
def delete_group(request, group_id):
    try:
        Group.objects.get(id=group_id).delete()
        return HttpResponse(status=204, headers={"HX-Trigger": "groupListReload"})
    except ProtectedError:
        error_message = (
            "Cannot delete group: it is in use by one or more relationships."
        )
        trigger = f'{{"showToast": {{"message": "{error_message}", "type": "error"}}}}'
        return HttpResponse(status=200, headers={"HX-Trigger": trigger})
