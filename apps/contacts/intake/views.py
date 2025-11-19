from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.contacts.contacts import get_list_data


@login_required
def index(request, contact_id):
    """Contact detail - Intake tab"""
    request.session["selected_contact_id"] = contact_id
    context = get_list_data(request)
    context["contact_subapp"] = "intake"
    return render(request, "contacts/main.html", context)
