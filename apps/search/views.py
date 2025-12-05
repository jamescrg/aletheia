from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from watson import search as watson

from apps.contacts.models import Contact
from apps.intakes.models import Intake
from apps.matters.models import Matter
from apps.matters.proceedings.models import Proceeding


@login_required
def index(request):
    context = {
        "app": "search",
        "action": "/search/results",
        "results": False,
    }
    return render(request, "search/content.html", context)


@login_required
def results(request):
    text = request.POST.get("search_text", "").strip()

    if not text:
        return render(
            request,
            "search/results.html",
            {"matters": None, "contacts": None, "proceedings": None, "intakes": None},
        )

    # Digits only - use exact matching for IDs and phone numbers
    if text.isdigit():
        matters = Matter.objects.filter(client_reference_id=text).order_by("name")
        contacts = Contact.objects.filter(
            Q(phone1__contains=text)
            | Q(phone2__contains=text)
            | Q(phone3__contains=text)
        ).order_by("name")
        proceedings = Proceeding.objects.filter(case_number__contains=text).order_by(
            "-status"
        )
        intakes = Intake.objects.filter(phone__contains=text).order_by("name")
    else:
        # Use watson for fuzzy search, limited to global search models
        search_results = watson.search(
            text,
            models=(Matter, Contact, Proceeding, Intake),
        )

        matters = []
        contacts = []
        proceedings = []
        intakes = []

        for result in search_results:
            obj = result.object
            if isinstance(obj, Matter):
                matters.append(obj)
            elif isinstance(obj, Contact):
                contacts.append(obj)
            elif isinstance(obj, Proceeding):
                proceedings.append(obj)
            elif isinstance(obj, Intake):
                intakes.append(obj)

    context = {
        "app": "search",
        "action": "/search/results",
        "results": True,
        "matters": matters,
        "contacts": contacts,
        "proceedings": proceedings,
        "intakes": intakes,
    }

    return render(request, "search/results.html", context)
