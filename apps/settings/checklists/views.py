from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.settings.checklists.forms import ChecklistTemplateForm
from apps.tasks.models import ChecklistTemplate, ChecklistTemplateItem


@login_required
def checklists_index(request):
    template_filter = request.session.get("settings_checklist_filter", "active")

    templates = ChecklistTemplate.objects.all()
    if template_filter == "active":
        templates = templates.filter(is_active=True)
    elif template_filter == "inactive":
        templates = templates.filter(is_active=False)

    context = {
        "subapp": "checklists",
        "templates": templates,
        "template_filter": template_filter,
    }

    return render(request, "settings/checklists/index.html", context)


@login_required
def checklist_template_list(request):
    template_filter = request.session.get("settings_checklist_filter", "active")

    templates = ChecklistTemplate.objects.all()
    if template_filter == "active":
        templates = templates.filter(is_active=True)
    elif template_filter == "inactive":
        templates = templates.filter(is_active=False)

    context = {
        "templates": templates,
        "template_filter": template_filter,
    }

    return render(request, "settings/checklists/template-table.html", context)


@login_required
def checklist_template_filter(request, status):
    request.session["settings_checklist_filter"] = status
    return HttpResponse(
        status=204, headers={"HX-Trigger": "checklistTemplateListReload"}
    )


@login_required
def add_checklist_template(request):
    if request.method == "POST":
        form = ChecklistTemplateForm(request.POST)

        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204, headers={"HX-Trigger": "checklistTemplateListReload"}
            )
    else:
        form = ChecklistTemplateForm()

    context = {
        "form": form,
    }

    return render(request, "settings/checklists/template-form.html", context)


@login_required
def edit_checklist_template(request, template_id):
    template = get_object_or_404(ChecklistTemplate, pk=template_id)

    if request.method == "POST":
        form = ChecklistTemplateForm(request.POST, instance=template)

        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204, headers={"HX-Trigger": "checklistTemplateListReload"}
            )
    else:
        form = ChecklistTemplateForm(instance=template)

    items = template.items.all()

    context = {
        "form": form,
        "template": template,
        "items": items,
    }

    return render(request, "settings/checklists/template-form.html", context)


@login_required
def delete_checklist_template(request, template_id):
    get_object_or_404(ChecklistTemplate, pk=template_id).delete()
    return HttpResponse(
        status=204, headers={"HX-Trigger": "checklistTemplateListReload"}
    )


@login_required
def add_template_item(request, template_id):
    template = get_object_or_404(ChecklistTemplate, pk=template_id)

    if request.method == "POST":
        description = request.POST.get("description", "").strip()
        if description:
            max_order = (
                template.items.order_by("-order")
                .values_list("order", flat=True)
                .first()
                or 0
            )
            ChecklistTemplateItem.objects.create(
                template=template,
                description=description,
                order=max_order + 1,
            )

    items = template.items.all()
    return render(
        request,
        "settings/checklists/template-items.html",
        {"template": template, "items": items},
    )


@login_required
def delete_template_item(request, item_id):
    item = get_object_or_404(ChecklistTemplateItem, pk=item_id)
    template = item.template
    item.delete()

    items = template.items.all()
    return render(
        request,
        "settings/checklists/template-items.html",
        {"template": template, "items": items},
    )
