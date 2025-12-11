from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from apps.matters.models import Matter


@login_required
def select_matter(request, matter_id):
    """Change the selected matter for the documents app."""
    matter = get_object_or_404(Matter, pk=matter_id)
    old_matter_id = request.session.get("documents_selected_matter")
    request.session["documents_selected_matter"] = matter.id

    # Only clear filters when actually changing to a different matter
    if old_matter_id != matter.id:
        filter_data = request.session.get("documents_filter", {})
        category = filter_data.get("category")
        request.session["documents_filter"] = {"category": category} if category else {}
        request.session.pop("selected_documents", None)

    return redirect("case:index")
