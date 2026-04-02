from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from apps.matters.models import PracticeArea
from apps.settings.matters.forms import PracticeAreaForm


@login_required
def matters_index(request):
    practice_area_filter = request.session.get(
        "settings_practice_area_filter", "active"
    )

    practice_areas = PracticeArea.objects.all().order_by("name")
    if practice_area_filter == "active":
        practice_areas = practice_areas.filter(is_active=True)
    elif practice_area_filter == "inactive":
        practice_areas = practice_areas.filter(is_active=False)

    context = {
        "app": "settings",
        "subapp": "matters",
        "practice_areas": practice_areas,
        "practice_area_filter": practice_area_filter,
    }

    return render(request, "settings/matters/index.html", context)


@login_required
def practice_area_list(request):
    practice_area_filter = request.session.get(
        "settings_practice_area_filter", "active"
    )

    practice_areas = PracticeArea.objects.all().order_by("name")
    if practice_area_filter == "active":
        practice_areas = practice_areas.filter(is_active=True)
    elif practice_area_filter == "inactive":
        practice_areas = practice_areas.filter(is_active=False)

    context = {
        "practice_areas": practice_areas,
        "practice_area_filter": practice_area_filter,
    }

    return render(request, "settings/matters/practice-area-table.html", context)


@login_required
def practice_area_filter(request, status):
    request.session["settings_practice_area_filter"] = status
    return HttpResponse(status=204, headers={"HX-Trigger": "practiceAreaListReload"})


@login_required
def add_practice_area(request):
    if request.method == "POST":
        form = PracticeAreaForm(request.POST)

        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204, headers={"HX-Trigger": "practiceAreaListReload"}
            )
    else:
        form = PracticeAreaForm()

    context = {
        "form": form,
    }

    return render(request, "settings/matters/practice-area-form.html", context)


@login_required
def edit_practice_area(request, practice_area_id):
    practice_area = PracticeArea.objects.get(id=practice_area_id)

    if request.method == "POST":
        form = PracticeAreaForm(request.POST, instance=practice_area)

        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204, headers={"HX-Trigger": "practiceAreaListReload"}
            )
    else:
        form = PracticeAreaForm(instance=practice_area)

    context = {
        "form": form,
        "practice_area": practice_area,
    }

    return render(request, "settings/matters/practice-area-form.html", context)


@login_required
def delete_practice_area(request, practice_area_id):
    PracticeArea.objects.get(id=practice_area_id).delete()
    return HttpResponse(status=204, headers={"HX-Trigger": "practiceAreaListReload"})
