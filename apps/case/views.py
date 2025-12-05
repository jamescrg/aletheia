import json

from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from watson import search as watson

from apps.case.filters import (
    FactsFilter,
    FilesFilter,
    HighlightsFilter,
    LabelsFilter,
    SearchFilter,
)
from apps.case.forms import (
    BulkFilesForm,
    FactForm,
    FilesForm,
    HighlightForm,
    LabelsForm,
)
from apps.case.generate_pdf import generate_facts_pdf
from apps.case.get_document_data import get_document_data, get_selected_matter
from apps.case.get_label_data import get_label_data
from apps.case.models import Document, Fact, Highlight, Label
from apps.management.pagination import CustomPaginator
from apps.matters.models import Matter


@login_required
def index(request):
    documents_data = get_document_data(request)

    context = {
        "app": "documents",
        "subapp": "documents",
    } | documents_data

    return render(request, "case/documents/main.html", context)


@login_required
def select_matter(request, matter_id):
    """Change the selected matter for the documents app."""
    matter = get_object_or_404(Matter, pk=matter_id)
    request.session["documents_selected_matter"] = matter.id
    # Clear any existing filters when changing matter
    request.session.pop("documents_filter", None)
    request.session.pop("selected_documents", None)
    return redirect("case:index")


@login_required
def documents_list(request):
    documents_data = get_document_data(request)

    context = {
        "app": "documents",
        "subapp": "documents",
    } | documents_data

    return render(request, "case/documents/list.html", context)


@login_required
def documents_filter(request):
    matter, matters = get_selected_matter(request)

    if request.method == "POST":
        # Convert QueryDict to regular dict, excluding CSRF token
        filter_data = {
            key: value
            for key, value in request.POST.items()
            if key != "csrfmiddlewaretoken"
        }
        request.session["documents_filter"] = filter_data

        return HttpResponse(status=204, headers={"HX-Trigger": "documentsChanged"})
    else:
        filter_data = request.session.get("documents_filter", {})

        # Build queryset filtered by matter
        queryset = (
            Document.objects.filter(matter=matter)
            .select_related("matter", "uploaded_by")
            .order_by("-uploaded_at")
            if matter
            else Document.objects.none()
        )

        filter_obj = FilesFilter(
            filter_data or {"order_by": "-uploaded_at"},
            queryset=queryset,
            matter=matter,
        )

        return render(request, "case/documents/filter.html", {"filter": filter_obj})


@login_required
def documents_filter_matter(request, matter_id):
    filter_data = request.session.get("documents_filter", {})
    filter_data["matter"] = matter_id

    request.session["documents_filter"] = filter_data

    return redirect("case:documents-list")


@login_required
def documents_filter_category(request, category=None):
    filter_data = request.session.get("documents_filter", {})
    if category:
        filter_data["category"] = category
    else:
        filter_data.pop("category", None)

    request.session["documents_filter"] = filter_data

    return redirect("case:documents-list")


@login_required
def documents_filter_keyword(request):
    filter_data = request.session.get("documents_filter", {})
    keyword = request.GET.get("keyword", "").strip()
    if keyword:
        filter_data["keyword"] = keyword
    else:
        filter_data.pop("keyword", None)

    request.session["documents_filter"] = filter_data

    # Render just the table partial (for search input updates)
    documents_data = get_document_data(request)
    return render(request, "case/documents/table.html", documents_data)


@login_required
def documents_filter_label(request, label_id):
    filter_data = request.session.get("documents_filter", {})
    filter_data["label"] = label_id

    request.session["documents_filter"] = filter_data

    return redirect("case:documents-list")


@login_required
def documents_filter_importance(request, importance_value):
    """Filter files by importance level."""
    filter_data = request.session.get("documents_filter", {})
    # Set to empty string when 0 (All) is selected, otherwise use the value
    filter_data["importance"] = "" if importance_value == 0 else importance_value

    request.session["documents_filter"] = filter_data

    return redirect("case:documents-list")


@login_required
def documents_sort(request, order):
    filter_data = request.session.get("documents_filter", {})

    current_order = filter_data.get("order_by", "")

    if current_order == order:
        new_order = f"-{order}" if not current_order.startswith("-") else order
    else:
        new_order = order

    filter_data["order_by"] = new_order
    request.session["documents_filter"] = filter_data

    return redirect("case:documents-list")


@login_required
def document_date(request, document_id):
    """Inline edit document date."""
    document = get_object_or_404(Document, id=document_id)

    if request.method == "POST":
        date_value = request.POST.get("date")
        if date_value:
            document.date = date_value
        else:
            document.date = None
        document.save()

        # Return the updated date display
        return render(
            request,
            "case/documents/date-display.html",
            {"document": document},
        )

    # GET - return the edit input
    return render(
        request,
        "case/documents/date-edit.html",
        {"document": document},
    )


@login_required
def document_category(request, document_id, category):
    """Set document category."""
    document = get_object_or_404(Document, id=document_id)
    document.category = category
    document.save()
    return redirect("case:documents-list")


@login_required
def document_proceeding(request, document_id, proceeding_id):
    """Set document proceeding."""
    from apps.matters.proceedings.models import Proceeding

    document = get_object_or_404(Document, id=document_id)

    if proceeding_id == 0:
        document.proceeding = None
    else:
        proceeding = get_object_or_404(Proceeding, id=proceeding_id)
        document.proceeding = proceeding

    document.save()
    return redirect("case:documents-list")


@login_required
def document_importance(request, document_id, importance):
    """Set document importance."""
    document = get_object_or_404(Document, id=document_id)
    document.importance = importance
    document.save()
    return redirect("case:documents-list")


@login_required
def highlight_importance(request, highlight_id, importance):
    """Set highlight importance."""
    highlight = get_object_or_404(Highlight, id=highlight_id)
    highlight.importance = importance
    highlight.save()
    return redirect("case:highlights-list")


@login_required
def documents_add(request, matter_id=None):
    # Get selected matter from session
    matter, matters = get_selected_matter(request)

    if not matter:
        return HttpResponse("No matter selected", status=400)

    if request.method == "POST":
        form = FilesForm(request.POST, matter=matter, use_required_attribute=False)
        uploaded_file = request.FILES.get("file")

        # Validate file is uploaded
        if not uploaded_file:
            form.add_error(None, "FILE_REQUIRED: Please select a file to upload.")

        if form.is_valid() and uploaded_file:
            # Two-phase save: first save without file to get PK
            document = form.save(commit=False)
            document.matter = matter
            document.uploaded_by = request.user
            document.save()  # Gets PK
            form.save_m2m()

            # Now save file with proper path using document.pk
            document.file = uploaded_file
            document.save()

            # Queue OCR for PDF files
            file_extension = uploaded_file.name.split(".")[-1].lower()
            if file_extension == "pdf":
                from django_q.tasks import async_task

                async_task(
                    "apps.case.tasks.process_document_ocr",
                    document.id,
                    task_name=f"OCR-{document.id}",
                    group="ocr_processing",
                )
            else:
                Document.objects.filter(id=document.id).update(
                    ocr_status="not_applicable"
                )

            return HttpResponse(status=204, headers={"HX-Trigger": "documentsChanged"})

        # Form has errors
        return render(
            request,
            "case/documents/form.html",
            {"form": form, "edit": False, "matter": matter},
        )

    else:
        form = FilesForm(matter=matter, use_required_attribute=False)

        return render(
            request,
            "case/documents/form.html",
            {"form": form, "edit": False, "matter": matter},
        )


@login_required
def documents_edit(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return HttpResponse(status=404)

    # Use the document's matter for the form
    matter = document.matter
    old_matter_id = document.matter_id

    if request.method == "POST":
        form = FilesForm(
            request.POST, instance=document, matter=matter, use_required_attribute=False
        )

        uploaded_file = request.FILES.get("file")

        if not uploaded_file and not document.file:
            form.add_error(None, "FILE_REQUIRED: Please select a file to upload.")

        if form.is_valid():
            old_file_path = document.file.name if document.file else None

            document = form.save(commit=False)
            document.uploaded_by = request.user

            # If new file uploaded, delete old and reset OCR fields
            if uploaded_file:
                if old_file_path:
                    default_storage.delete(old_file_path)

                document.file = uploaded_file
                document.ocr_status = "pending"
                document.ocr_text = None
                document.ocr_error = None
                document.ocr_processed_at = None
                document.page_count = None
                document.ocr_pages_done = 0
            # If matter changed (and no new file), move file to new matter's folder
            elif document.matter_id != old_matter_id and old_file_path:
                file_extension = old_file_path.split(".")[-1].lower()
                new_file_path = (
                    f"case/{document.matter_id}/{document.pk}.{file_extension}"
                )

                # Read old file, save to new path, delete old
                with default_storage.open(old_file_path, "rb") as f:
                    file_content = f.read()
                default_storage.save(new_file_path, ContentFile(file_content))
                default_storage.delete(old_file_path)
                document.file.name = new_file_path

            document.save()
            form.save_m2m()

            # Queue OCR for new PDF file
            if uploaded_file:
                file_extension = uploaded_file.name.split(".")[-1].lower()
                if file_extension == "pdf":
                    from django_q.tasks import async_task

                    async_task(
                        "apps.case.tasks.process_document_ocr",
                        document.id,
                        task_name=f"OCR-{document.id}",
                        group="ocr_processing",
                    )
                else:
                    Document.objects.filter(id=document.id).update(
                        ocr_status="not_applicable"
                    )

            return HttpResponse(
                status=204,
                headers={"HX-Trigger": "documentsChanged"},
            )

        # Form has errors
        return render(
            request,
            "case/documents/form.html",
            {"form": form, "document": document, "edit": True, "matter": matter},
        )
    else:
        form = FilesForm(instance=document, matter=matter, use_required_attribute=False)

        return render(
            request,
            "case/documents/form.html",
            {"form": form, "document": document, "edit": True, "matter": matter},
        )


@login_required
def bulk_documents_update(request):
    matter, matters = get_selected_matter(request)
    selected_documents = request.session.get("selected_documents", [])

    if not selected_documents:
        return HttpResponse(status=400, content="No documents selected.")

    if request.method == "POST":
        form = BulkFilesForm(request.POST, matter=matter, use_required_attribute=False)

        if form.is_valid():
            proceeding = form.cleaned_data.get("proceeding")
            labels = form.cleaned_data.get("labels")

            documents = Document.objects.filter(id__in=selected_documents)

            for document in documents:
                if proceeding:
                    document.proceeding = proceeding
                if labels:
                    document.labels.set(labels)

                document.save()

            request.session["selected_documents"] = []

            return HttpResponse(
                status=204,
                headers={"HX-Trigger": "documentsChanged"},
            )

        return render(
            request,
            "case/documents/bulk_form.html",
            {"form": form, "matter": matter},
        )
    else:
        form = BulkFilesForm(matter=matter, use_required_attribute=False)

        return render(
            request,
            "case/documents/bulk_form.html",
            {"form": form, "matter": matter},
        )


@login_required
def documents_delete(request, document_id):
    try:
        Document.objects.get(id=document_id).delete()

        selected_documents = request.session.get("selected_documents", [])
        if document_id in selected_documents:
            selected_documents.remove(document_id)

            request.session["selected_documents"] = selected_documents
    except Document.DoesNotExist:
        return HttpResponse(status=404)

    return HttpResponse(status=204, headers={"HX-Trigger": "documentsChanged"})


@login_required
def download_document(request, document_id):
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        return HttpResponse(status=404)

    response = HttpResponse(
        document.file,
        content_type="application/octet-stream",
    )

    file_extension = document.file.name.split(".")[-1]
    full_file_name = f"{document.name}.{file_extension}"

    if document.category == "Record" and document.date:
        full_file_name = f"{document.date}_{full_file_name}"

    response["Content-Disposition"] = f'attachment; filename="{full_file_name}"'
    response["Content-Length"] = document.file.size

    return response


@login_required
def serve_document(request, document_id):
    """Serve document inline for PDF viewer (avoids CORS issues with S3)."""
    document = get_object_or_404(Document, id=document_id)

    file_content = document.file.read()

    response = HttpResponse(file_content, content_type="application/pdf")
    response["Content-Length"] = len(file_content)
    response["Cache-Control"] = "private, max-age=3600"

    return response


@login_required
def get_proceedings_and_labels(request):
    matter_id = request.GET.get("matter")

    proceedings = []
    labels = []

    if matter_id:
        try:
            matter = Matter.objects.get(id=matter_id)

            proceedings = matter.proceeding_set.all().order_by("date_filed")
            # Include global labels + matter-specific labels
            labels = Label.objects.filter(Q(matter=None) | Q(matter=matter)).order_by(
                "matter", "name"
            )
        except Matter.DoesNotExist:
            pass
    else:
        # No matter selected - show only global labels
        labels = Label.objects.filter(matter=None).order_by("name")

    proceedings_html = render(
        request,
        "case/documents/proceeding_options.html",
        {"proceedings": proceedings},
    ).content.decode("utf-8")

    labels_html = render(
        request,
        "case/documents/label_options.html",
        {"labels": labels},
    ).content.decode("utf-8")

    combined_html = f"""
        <select id="id_proceeding" hx-swap-oob="outerHTML" name="proceeding">
            {proceedings_html}
        </select>
        <select id="id_labels" hx-swap-oob="outerHTML" multiple class="span2" name="labels">
            {labels_html}
        </select>
    """

    return HttpResponse(combined_html)


@login_required
def labels_index(request):
    label_data = get_label_data(request)

    context = {
        "app": "documents",
        "subapp": "labels",
    } | label_data

    return render(request, "case/labels/main.html", context)


@login_required
def labels_list(request):
    label_data = get_label_data(request)

    context = {
        "app": "documents",
        "subapp": "labels",
    } | label_data

    return render(request, "case/labels/list.html", context)


@login_required
def add_label(request):
    if request.method == "POST":
        form = LabelsForm(request.POST, use_required_attribute=False)
        form.fields["matter"].queryset = Matter.objects.filter(status="Open").order_by(
            "name"
        )

        if form.is_valid():
            form.save()

            return HttpResponse(status=204, headers={"HX-Trigger": "labelsChanged"})

        return render(request, "case/labels/form.html", {"form": form, "edit": False})
    else:
        form = LabelsForm(use_required_attribute=False)
        form.fields["matter"].queryset = Matter.objects.filter(status="Open").order_by(
            "name"
        )

        return render(request, "case/labels/form.html", {"form": form, "edit": False})


@login_required
def edit_label(request, label_id):
    try:
        label = Label.objects.get(id=label_id)
    except Label.DoesNotExist:
        return HttpResponse(status=404)

    matter_list = Matter.objects.filter(status="Open").order_by("name")

    # Include closed matter if label belongs to one
    if label.matter and label.matter not in matter_list:
        matter_list = matter_list | Matter.objects.filter(pk=label.matter.id)

    if request.method == "POST":
        form = LabelsForm(request.POST, instance=label, use_required_attribute=False)

        form.fields["matter"].queryset = matter_list

        if form.is_valid():
            form.save()

            return HttpResponse(
                status=204,
                headers={"HX-Trigger": "labelsChanged"},
            )

        return render(
            request,
            "case/labels/form.html",
            {"form": form, "label": label, "edit": True},
        )
    else:
        form = LabelsForm(instance=label, use_required_attribute=False)

        form.fields["matter"].queryset = matter_list

        return render(
            request,
            "case/labels/form.html",
            {"form": form, "label": label, "edit": True},
        )


@login_required
def labels_filter(request):
    if request.method == "POST":
        request.session["labels_filter"] = request.POST

        return HttpResponse(status=204, headers={"HX-Trigger": "labelsChanged"})
    else:
        filter_data = request.session.get("labels_filter", {})

        if filter_data:
            filter = LabelsFilter(
                filter_data,
                queryset=Label.objects.all()
                .select_related("matter")
                .order_by("matter__name", "name"),
            )
        else:
            default_filter = {"order_by": "name"}

            filter = LabelsFilter(
                default_filter,
                queryset=Label.objects.all().select_related("matter").order_by("name"),
            )

        return render(request, "case/labels/filter.html", {"filter": filter})


@login_required
def labels_sort(request, order):
    filter_data = request.session.get("labels_filter", {})

    current_order = filter_data.get("order_by", "")

    if current_order == order:
        new_order = f"-{order}" if not current_order.startswith("-") else order
    else:
        new_order = order

    filter_data["order_by"] = new_order
    request.session["labels_filter"] = filter_data

    return HttpResponse(status=204, headers={"HX-Trigger": "labelsChanged"})


@login_required
def delete_label(request, label_id):
    try:
        Label.objects.get(id=label_id).delete()
    except Label.DoesNotExist:
        return HttpResponse(status=404)

    return HttpResponse(status=204, headers={"HX-Trigger": "labelsChanged"})


def _get_object_for_labels(object_type, object_id, view=None):
    """Helper to get object and matter by type for label operations."""
    if object_type == "document":
        obj = get_object_or_404(Document, id=object_id)
        matter = obj.matter
        row_template = "case/documents/row.html"
        context_key = "document"
    elif object_type == "highlight":
        obj = get_object_or_404(Highlight, id=object_id)
        matter = obj.document.matter if obj.document else None
        # Use table row template if view=table, otherwise card template
        if view == "table":
            row_template = "case/highlights/highlight-row.html"
        else:
            row_template = "case/highlights/row.html"
        context_key = "highlight"
    elif object_type == "fact":
        obj = get_object_or_404(Fact, id=object_id)
        matter = obj.matter
        row_template = "case/facts/fact-row.html"
        context_key = "fact"
    else:
        return None, None, None, None
    return obj, matter, row_template, context_key


@login_required
def labels_apply_modal(request, object_type, object_id):
    """Open modal to apply labels to an object."""
    obj, matter, _, _ = _get_object_for_labels(object_type, object_id)
    if obj is None:
        return HttpResponse("Invalid object type", status=400)

    view = request.GET.get("view", "")
    return render(
        request,
        "case/labels/apply-modal.html",
        {"object": obj, "object_type": object_type, "matter": matter, "view": view},
    )


@login_required
def labels_search(request, object_type, object_id):
    """Search labels for apply modal."""
    obj, matter, _, _ = _get_object_for_labels(object_type, object_id)
    if obj is None:
        return HttpResponse("Invalid object type", status=400)

    query = request.GET.get("q", "").strip()
    view = request.GET.get("view", "")

    # Get available labels (global + matter-specific)
    if matter:
        labels = Label.objects.filter(Q(matter=None) | Q(matter=matter))
    else:
        labels = Label.objects.filter(matter=None)

    # Filter by search query
    if query:
        labels = labels.filter(name__icontains=query)

    # Exclude already-applied labels
    existing_label_ids = obj.labels.values_list("id", flat=True)
    labels = labels.exclude(id__in=existing_label_ids)

    # Order: global first, then matter-specific, alphabetically
    labels = labels.order_by("matter", "name")

    return render(
        request,
        "case/labels/apply-results.html",
        {"labels": labels, "object": obj, "object_type": object_type, "view": view},
    )


@login_required
def add_label_to(request, object_type, object_id):
    """Add a label to an object."""
    view = request.POST.get("view")
    obj, matter, row_template, context_key = _get_object_for_labels(
        object_type, object_id, view
    )
    if obj is None:
        return HttpResponse("Invalid object type", status=400)

    label_id = request.POST.get("label_id")
    if label_id:
        try:
            label = Label.objects.get(id=label_id)
            obj.labels.add(label)
        except Label.DoesNotExist:
            pass

    context = {context_key: obj, "importance_choices": range(1, 11)}
    return render(request, row_template, context)


@login_required
def remove_label_from(request, object_type, object_id):
    """Remove a label from an object."""
    view = request.POST.get("view")
    obj, matter, row_template, context_key = _get_object_for_labels(
        object_type, object_id, view
    )
    if obj is None:
        return HttpResponse("Invalid object type", status=400)

    label_id = request.POST.get("label_id")
    if label_id:
        try:
            label = Label.objects.get(id=label_id)
            obj.labels.remove(label)
        except Label.DoesNotExist:
            pass

    context = {context_key: obj, "importance_choices": range(1, 11)}
    return render(request, row_template, context)


@login_required
def labels_create_and_apply(request, object_type, object_id):
    """Create a new label and apply it to an object."""
    view = request.POST.get("view")
    obj, matter, row_template, context_key = _get_object_for_labels(
        object_type, object_id, view
    )
    if obj is None:
        return HttpResponse("Invalid object type", status=400)

    name = request.POST.get("name", "").strip()
    color = request.POST.get("color", "gray")

    if name:
        label = Label.objects.create(matter=matter, name=name, color=color)
        obj.labels.add(label)

    context = {context_key: obj, "importance_choices": range(1, 11)}
    return render(request, row_template, context)


@login_required
def toggle_document_select(request, document_id):
    selected_documents = request.session.get("selected_documents", [])

    if document_id in selected_documents:
        selected_documents.remove(document_id)
    else:
        selected_documents.append(document_id)

    request.session["selected_documents"] = selected_documents

    return HttpResponse(status=204, headers={"HX-Trigger": "documentsChanged"})


@login_required
def clear_document_selection(request):
    request.session["selected_documents"] = []

    return HttpResponse(status=204, headers={"HX-Trigger": "documentsChanged"})


@login_required
def document_row(request, document_id):
    """Return a single file row (for HTMX polling of OCR status)."""
    document = get_object_or_404(Document, id=document_id)
    selected_documents = request.session.get("selected_documents", [])
    matter = document.matter
    proceedings = matter.proceeding_set.all().order_by("forum", "case_number")

    return render(
        request,
        "case/documents/row.html",
        {
            "document": document,
            "selected_documents": selected_documents,
            "proceedings": proceedings,
        },
    )


@login_required
def documents_edit_name(request, document_id):
    """Edit file name inline."""
    document = get_object_or_404(Document, id=document_id)

    if request.method == "POST":
        document.name = request.POST.get("name", document.name)
        document.save()

        selected_documents = request.session.get("selected_documents", [])
        proceedings = document.matter.proceeding_set.all().order_by(
            "forum", "case_number"
        )

        return render(
            request,
            "case/documents/row.html",
            {
                "document": document,
                "selected_documents": selected_documents,
                "proceedings": proceedings,
            },
        )

    # GET - return the input field
    return render(
        request,
        "case/documents/edit-name.html",
        {"document": document},
    )


@login_required
def ocr_badge(request, document_id):
    """Return OCR status badge (for HTMX polling)."""
    document = get_object_or_404(Document, id=document_id)

    return render(
        request,
        "case/documents/ocr-badge.html",
        {"document": document},
    )


# PDF Viewer and Highlighting Views


@login_required
def document_viewer(request, document_id):
    """PDF viewer page for a document."""
    document = get_object_or_404(Document, id=document_id)
    highlights = document.highlights.all().order_by("page_number", "created_at")

    # Get query params for initial navigation
    initial_page = request.GET.get("page", 1)
    initial_highlight = request.GET.get("highlight")

    try:
        initial_page = int(initial_page)
    except (TypeError, ValueError):
        initial_page = 1

    try:
        initial_highlight = int(initial_highlight) if initial_highlight else None
    except (TypeError, ValueError):
        initial_highlight = None

    # Serialize highlights for JavaScript
    highlights_json = json.dumps(
        [
            {
                "id": h.id,
                "slug": h.slug,
                "text": h.text,
                "page_number": h.page_number,
                "coordinates": h.coordinates,
                "color": h.color,
            }
            for h in highlights
        ]
    )

    context = {
        "document": document,
        "highlights": highlights,
        "highlights_json": highlights_json,
        "initial_page": initial_page,
        "initial_highlight": initial_highlight,
    }

    return render(request, "case/viewer.html", context)


@login_required
def ocr_status(request, document_id):
    """Return OCR status for polling."""
    document = get_object_or_404(Document, id=document_id)

    return JsonResponse(
        {
            "status": document.ocr_status,
            "error": document.ocr_error,
            "processed_at": (
                document.ocr_processed_at.isoformat()
                if document.ocr_processed_at
                else None
            ),
            "page_count": document.page_count,
        }
    )


@login_required
@require_POST
def add_highlight(request, document_id):
    """Create a new highlight."""
    document = get_object_or_404(Document, id=document_id)

    slug = request.POST.get("slug", "").strip()
    if not slug:
        return JsonResponse({"error": "Slug is required"}, status=400)

    try:
        coordinates = json.loads(request.POST.get("coordinates", "{}"))

        paragraph_number = request.POST.get("paragraph_number", "").strip() or None

        highlight = Highlight.objects.create(
            document=document,
            slug=slug,
            text=request.POST.get("text"),
            page_number=int(request.POST.get("page_number")),
            paragraph_number=paragraph_number,
            coordinates=coordinates,
            color=request.POST.get("color", "yellow"),
            importance=5,
            created_by=request.user,
        )

        return JsonResponse(
            {
                "id": highlight.id,
                "slug": highlight.slug,
                "text": highlight.text,
                "page_number": highlight.page_number,
                "paragraph_number": highlight.paragraph_number,
                "citation": highlight.citation,
                "coordinates": highlight.coordinates,
                "color": highlight.color,
                "importance": highlight.importance,
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
@require_POST
def delete_highlight(request, highlight_id):
    """Delete a highlight."""
    highlight = get_object_or_404(Highlight, id=highlight_id)

    # Check permission (creator or allow all authenticated users for now)
    highlight.delete()

    # Return empty response for HTMX (removes the row), JSON for JS
    if request.headers.get("HX-Request"):
        return HttpResponse("")
    return JsonResponse({"success": True})


@login_required
def edit_highlight(request, highlight_id):
    """Edit a highlight's slug, color, importance, and text."""
    highlight = get_object_or_404(Highlight, id=highlight_id)
    is_viewer_context = request.GET.get("context") == "viewer"

    if request.method == "POST":
        form = HighlightForm(request.POST, instance=highlight)
        if form.is_valid():
            form.save()
            # Return JSON for viewer context, HX-Trigger for highlights list
            if is_viewer_context:
                return JsonResponse(
                    {
                        "id": highlight.id,
                        "slug": highlight.slug,
                        "color": highlight.color,
                        "importance": highlight.importance,
                        "text": highlight.text,
                    }
                )
            return HttpResponse(
                status=204,
                headers={"HX-Trigger": "highlightsChanged"},
            )
    else:
        form = HighlightForm(instance=highlight)

    return render(
        request,
        "case/highlights/edit.html",
        {"highlight": highlight, "form": form},
    )


@login_required
def highlight_link(request, highlight_id):
    """Redirect to viewer at specific highlight location."""
    highlight = get_object_or_404(Highlight, id=highlight_id)

    from django.urls import reverse

    viewer_url = reverse("case:viewer", args=[highlight.document_id])
    return redirect(
        f"{viewer_url}?page={highlight.page_number}&highlight={highlight.id}"
    )


@login_required
@require_POST
def retry_ocr(request, document_id):
    """Retry OCR for a failed document."""
    document = get_object_or_404(Document, id=document_id)

    if document.ocr_status not in ["failed", "pending"]:
        return JsonResponse(
            {"error": "OCR cannot be retried for this document"}, status=400
        )

    from django_q.tasks import async_task

    async_task(
        "apps.case.tasks.process_document_ocr",
        document.id,
        task_name=f"OCR-Retry-{document.id}",
        group="ocr_processing",
    )

    document.ocr_status = "pending"
    document.save(update_fields=["ocr_status"])

    return JsonResponse({"success": True, "status": "pending"})


# =============================================================================
# Highlights Subapp
# =============================================================================


def get_highlights_data(request, matter):
    """Get highlights data with filters applied from session."""
    filter_data = request.session.get("highlights_filter", {})

    highlights = []
    documents = []
    selected_document = None

    # Extract values from filter_data (handles both list and string formats)
    def get_filter_value(key):
        val = filter_data.get(key, "")
        return val[0] if isinstance(val, list) else val

    keyword = get_filter_value("keyword")
    order_by = get_filter_value("order_by")
    document_id = get_filter_value("document")

    if matter:
        highlights = Highlight.objects.filter(document__matter=matter).select_related(
            "document", "document__matter", "created_by"
        )
        documents = Document.objects.filter(matter=matter).order_by("name")

        # Apply filters using HighlightsFilter
        highlight_filter = HighlightsFilter(
            filter_data, queryset=highlights, matter=matter
        )
        highlights = highlight_filter.qs

        # Get selected document for template
        if document_id:
            selected_document = documents.filter(id=document_id).first()

        # Handle custom ordering with secondary sorts
        if order_by == "date":
            highlights = highlights.order_by("document__date", "slug", "page_number")
        elif order_by == "-date":
            highlights = highlights.order_by("-document__date", "slug", "page_number")
        elif order_by == "slug":
            highlights = highlights.order_by("slug", "document__date", "page_number")
        elif order_by == "-slug":
            highlights = highlights.order_by("-slug", "document__date", "page_number")
        elif order_by == "importance":
            highlights = highlights.order_by("importance", "document__date", "slug")
        elif order_by == "-importance":
            highlights = highlights.order_by("-importance", "document__date", "slug")
        elif not order_by:
            # Default: order by date, then slug
            highlights = highlights.order_by("document__date", "slug", "page_number")

    # Determine current_order for template (strip leading '-' for base field)
    current_order = order_by if order_by else "date"

    # Get importance filter value
    importance_value = get_filter_value("importance")
    importance_value = (
        int(importance_value) if importance_value not in (None, "", 0) else None
    )

    # Paginate highlights
    pagination = CustomPaginator(
        highlights, per_page=10, request=request, session_key="highlights_pagination"
    )
    highlights = pagination.get_object_list()

    return {
        "highlights": highlights,
        "pagination": pagination,
        "session_key": "highlights_pagination",
        "trigger_key": "highlightsChanged",
        "documents": documents,
        "selected_document": selected_document,
        "keyword": keyword,
        "order_by": order_by,
        "current_order": current_order,
        "importance_choices": range(1, 11),
        "importances": list(range(1, 11)),
        "importance_value": importance_value,
        "selected_importance": (
            f"Importance {importance_value}" if importance_value else ""
        ),
    }


@login_required
def highlights_index(request):
    """Main highlights list view."""
    matter, matters = get_selected_matter(request)

    context = {
        "app": "documents",
        "subapp": "highlights",
        "matter": matter,
        "matters": matters,
    } | get_highlights_data(request, matter)

    return render(request, "case/highlights/main.html", context)


@login_required
def highlights_list(request):
    """HTMX partial for highlights list."""
    matter, matters = get_selected_matter(request)

    context = {
        "app": "documents",
        "subapp": "highlights",
        "matter": matter,
        "matters": matters,
    } | get_highlights_data(request, matter)

    return render(request, "case/highlights/list.html", context)


@login_required
def highlights_filter_document(request, document_id=None):
    """Filter highlights by document (inline dropdown)."""
    filter_data = request.session.get("highlights_filter", {})

    if document_id:
        filter_data["document"] = document_id  # Store as int
    else:
        filter_data["document"] = ""  # Empty string for "All"

    request.session["highlights_filter"] = filter_data
    request.session["highlights_pagination"] = 1  # Reset to page 1

    return HttpResponse(status=204, headers={"HX-Trigger": "highlightsChanged"})


@login_required
def highlights_for_document(request, document_id):
    """Set document filter and redirect to highlights page."""
    filter_data = request.session.get("highlights_filter", {})
    filter_data["document"] = document_id
    request.session["highlights_filter"] = filter_data

    return redirect("case:highlights-index")


@login_required
def highlights_filter_keyword(request):
    """Filter highlights by keyword (inline search)."""
    matter, _ = get_selected_matter(request)
    filter_data = request.session.get("highlights_filter", {})
    keyword = request.POST.get("keyword", "").strip()

    filter_data["keyword"] = keyword  # Store as simple string

    request.session["highlights_filter"] = filter_data
    request.session["highlights_pagination"] = 1  # Reset to page 1

    # Render just the cards partial (for search input updates)
    context = get_highlights_data(request, matter)
    return render(request, "case/highlights/cards.html", context)


@login_required
def highlights_filter_importance(request, importance_value):
    """Filter highlights by importance level."""
    filter_data = request.session.get("highlights_filter", {})
    # Set to empty string when 0 (All) is selected, otherwise use the value
    filter_data["importance"] = "" if importance_value == 0 else importance_value

    request.session["highlights_filter"] = filter_data
    request.session["highlights_pagination"] = 1  # Reset to page 1

    return redirect("case:highlights-list")


@login_required
def highlights_filter(request):
    """Filter modal for highlights - GET shows modal, POST saves to session."""
    matter, matters = get_selected_matter(request)

    if request.method == "POST":
        # Store POST values directly (matching tasks pattern)
        filter_data = {
            key: value
            for key, value in request.POST.items()
            if key != "csrfmiddlewaretoken"
        }
        request.session["highlights_filter"] = filter_data
        request.session["highlights_pagination"] = 1  # Reset to page 1
        return HttpResponse(status=204, headers={"HX-Trigger": "highlightsChanged"})

    # GET - show filter modal
    filter_data = request.session.get("highlights_filter", {})

    queryset = (
        Highlight.objects.filter(document__matter=matter)
        if matter
        else Highlight.objects.none()
    )

    filter_obj = HighlightsFilter(filter_data, queryset=queryset, matter=matter)

    context = {
        "filter": filter_obj,
    }

    return render(request, "case/highlights/filter.html", context)


@login_required
def highlights_filter_sort(request, order):
    """Sort highlights by field, toggling asc/desc."""
    filter_data = request.session.get("highlights_filter", {})
    current_order = filter_data.get("order_by", "")

    # Toggle direction if same field
    if current_order == order:
        filter_data["order_by"] = f"-{order}"
    elif current_order == f"-{order}":
        filter_data["order_by"] = order
    else:
        filter_data["order_by"] = order

    request.session["highlights_filter"] = filter_data
    request.session["highlights_pagination"] = 1  # Reset to page 1

    return HttpResponse(status=204, headers={"HX-Trigger": "highlightsChanged"})


@login_required
def highlights_filter_default(request):
    """Reset highlights filter to defaults."""
    request.session["highlights_filter"] = {
        "document": "",
        "keyword": "",
        "order_by": "document",
    }
    return redirect("case:highlights-index")


# =============================================================================
# Facts Subapp
# =============================================================================


def get_facts_data(request, matter):
    """Get facts data with filters applied from session."""
    filter_data = request.session.get("facts_filter", {})

    facts = []
    if matter:
        queryset = Fact.objects.filter(matter=matter).order_by("date", "time")

        # Apply filters if present
        if filter_data:
            facts_filter = FactsFilter(filter_data, queryset=queryset)
            facts = facts_filter.qs
        else:
            facts = queryset

    # Get current sort order
    current_order = filter_data.get("order_by", "date")
    if isinstance(current_order, list):
        current_order = current_order[0] if current_order else "date"

    # Get keyword value
    keyword = filter_data.get("keyword", "")
    if isinstance(keyword, list):
        keyword = keyword[0] if keyword else ""

    # Get importance filter value
    importance_value = filter_data.get("importance")
    importance_value = (
        int(importance_value) if importance_value not in (None, "", 0) else None
    )

    return {
        "facts": facts,
        "current_order": current_order,
        "keyword": keyword,
        "importances": list(range(1, 11)),
        "importance_value": importance_value,
        "selected_importance": (
            f"Importance {importance_value}" if importance_value else ""
        ),
    }


@login_required
def facts_index(request):
    """Main facts view."""
    matter, matters = get_selected_matter(request)

    context = {
        "app": "documents",
        "subapp": "facts",
        "matter": matter,
        "matters": matters,
    } | get_facts_data(request, matter)

    return render(request, "case/facts/main.html", context)


@login_required
def facts_list(request):
    """HTMX partial for facts list."""
    matter, matters = get_selected_matter(request)

    context = {
        "app": "documents",
        "subapp": "facts",
        "matter": matter,
        "matters": matters,
    } | get_facts_data(request, matter)

    return render(request, "case/facts/list.html", context)


@login_required
def facts_add(request):
    """Add a new fact."""
    matter, matters = get_selected_matter(request)

    if not matter:
        return HttpResponse("No matter selected", status=400)

    if request.method == "POST":
        form = FactForm(request.POST, use_required_attribute=False)
        if form.is_valid():
            fact = form.save(commit=False)
            fact.user = request.user
            fact.matter = matter
            fact.save()

            return HttpResponse(status=204, headers={"HX-Trigger": "factsChanged"})
    else:
        form = FactForm(use_required_attribute=False)

    context = {
        "app": "documents",
        "subapp": "facts",
        "matter": matter,
        "form": form,
        "action": "Add",
    }

    return render(request, "case/facts/form.html", context)


@login_required
def facts_edit(request, fact_id):
    """Edit a fact."""
    matter, matters = get_selected_matter(request)
    fact = get_object_or_404(Fact, pk=fact_id)

    if request.method == "POST":
        form = FactForm(request.POST, instance=fact, use_required_attribute=False)
        if form.is_valid():
            fact = form.save(commit=False)
            fact.user = request.user
            fact.save()

            return HttpResponse(status=204, headers={"HX-Trigger": "factsChanged"})
    else:
        form = FactForm(instance=fact, use_required_attribute=False)

    context = {
        "app": "documents",
        "subapp": "facts",
        "matter": matter,
        "fact": fact,
        "form": form,
        "action": "Edit",
    }

    return render(request, "case/facts/form.html", context)


@login_required
@require_POST
def facts_delete(request, fact_id):
    """Delete a fact."""
    fact = get_object_or_404(Fact, pk=fact_id)
    fact.delete()

    return HttpResponse(status=204, headers={"HX-Trigger": "factsChanged"})


@login_required
def facts_print(request):
    """Print view for facts."""
    matter, matters = get_selected_matter(request)

    facts = []
    if matter:
        facts = Fact.objects.filter(matter=matter).order_by("date", "time")

    context = {
        "matter": matter,
        "facts": facts,
    }
    return render(request, "case/facts/print.html", context)


@login_required
def facts_pdf(request):
    """Generate PDF for facts."""
    import os
    from datetime import datetime

    matter, matters = get_selected_matter(request)

    if not matter:
        return HttpResponse("No matter selected", status=400)

    file = generate_facts_pdf(matter.id, request)

    current_date = datetime.now().strftime("%Y-%m-%d")

    with open(file.name, "rb") as pdf:
        response = HttpResponse(pdf.read(), content_type="application/pdf")
        filename = f'filename="Facts - {matter.name} - {current_date}.pdf"'
        response["Content-Disposition"] = f"attachment; {filename}"

    os.unlink(file.name)

    return response


@login_required
def facts_edit_description(request, fact_id):
    """Inline edit fact description."""
    matter, matters = get_selected_matter(request)
    fact = get_object_or_404(Fact, pk=fact_id)
    context = {"fact": fact, "matter": matter}
    return render(request, "case/facts/edit-description.html", context)


@login_required
def facts_update_description(request, fact_id):
    """Update fact description inline."""
    matter, matters = get_selected_matter(request)
    fact = get_object_or_404(Fact, pk=fact_id)
    fact.description = request.POST.get("description")
    fact.save()

    context = {
        "matter": matter,
        "fact": fact,
    }
    return render(request, "case/facts/fact-row.html", context)


@login_required
def fact_sources_modal(request, fact_id):
    """Render modal for managing fact sources (documents and highlights)."""
    matter, matters = get_selected_matter(request)
    fact = get_object_or_404(Fact, pk=fact_id)
    context = {
        "fact": fact,
        "matter": matter,
    }
    return render(request, "case/facts/sources-modal.html", context)


@login_required
def fact_sources_search(request, fact_id):
    """Search documents and highlights for fact sources."""
    matter, matters = get_selected_matter(request)
    fact = get_object_or_404(Fact, pk=fact_id)
    query = request.GET.get("q", "").strip()

    documents = []
    highlights = []

    if query and matter:
        # Search documents by name
        documents = Document.objects.filter(matter=matter, name__icontains=query)[:10]

        # Search highlights by slug or text
        from django.db.models import Q

        highlights = (
            Highlight.objects.filter(document__matter=matter)
            .filter(Q(slug__icontains=query) | Q(text__icontains=query))
            .select_related("document")[:10]
        )

    context = {
        "fact": fact,
        "documents": documents,
        "highlights": highlights,
        "query": query,
    }
    return render(request, "case/facts/sources-results.html", context)


@login_required
@require_POST
def fact_add_source(request, fact_id):
    """Add a document or highlight as a source to a fact."""
    matter, matters = get_selected_matter(request)
    fact = get_object_or_404(Fact, pk=fact_id)

    source_type = request.POST.get("type")
    source_id = request.POST.get("id")

    if source_type == "document":
        document = get_object_or_404(Document, pk=source_id)
        fact.documents.add(document)
    elif source_type == "highlight":
        highlight = get_object_or_404(Highlight, pk=source_id)
        fact.highlights.add(highlight)

    context = {
        "matter": matter,
        "fact": fact,
    }
    return render(request, "case/facts/fact-row.html", context)


@login_required
@require_POST
def fact_remove_source(request, fact_id):
    """Remove a document or highlight source from a fact."""
    matter, matters = get_selected_matter(request)
    fact = get_object_or_404(Fact, pk=fact_id)

    source_type = request.POST.get("type")
    source_id = request.POST.get("id")

    if source_type == "document":
        document = get_object_or_404(Document, pk=source_id)
        fact.documents.remove(document)
    elif source_type == "highlight":
        highlight = get_object_or_404(Highlight, pk=source_id)
        fact.highlights.remove(highlight)

    context = {
        "matter": matter,
        "fact": fact,
    }
    return render(request, "case/facts/fact-row.html", context)


@login_required
def fact_importance(request, fact_id, importance):
    """Set fact importance."""
    fact = get_object_or_404(Fact, pk=fact_id)
    fact.importance = importance
    fact.save()
    return redirect("case:facts-list")


@login_required
def facts_filter(request):
    """Filter modal for facts - GET shows modal, POST saves to session."""
    matter, matters = get_selected_matter(request)

    if request.method == "POST":
        filter_data = {
            key: value
            for key, value in request.POST.items()
            if key != "csrfmiddlewaretoken"
        }
        request.session["facts_filter"] = filter_data
        request.session.modified = True
        return HttpResponse(status=204, headers={"HX-Trigger": "factsChanged"})

    # GET - show filter modal
    filter_data = request.session.get("facts_filter", {})

    queryset = Fact.objects.filter(matter=matter) if matter else Fact.objects.none()

    filter_obj = FactsFilter(filter_data, queryset=queryset)

    return render(request, "case/facts/filter.html", {"filter": filter_obj})


@login_required
def facts_sort(request, order):
    """Sort facts by field, toggling asc/desc."""
    filter_data = request.session.get("facts_filter", {})

    current_order = filter_data.get("order_by", "")

    if current_order == order:
        new_order = f"-{order}" if not current_order.startswith("-") else order
    else:
        new_order = order

    filter_data["order_by"] = new_order
    request.session["facts_filter"] = filter_data
    request.session.modified = True

    return redirect("case:facts-list")


@login_required
def facts_filter_keyword(request):
    """Filter facts by keyword (inline search)."""
    matter, _ = get_selected_matter(request)
    filter_data = request.session.get("facts_filter", {})
    keyword = request.GET.get("keyword", "").strip()

    if keyword:
        filter_data["keyword"] = keyword
    else:
        filter_data.pop("keyword", None)

    request.session["facts_filter"] = filter_data

    # Render just the table partial (for search input updates)
    context = get_facts_data(request, matter)
    return render(request, "case/facts/table.html", context)


@login_required
def facts_filter_importance(request, importance_value):
    """Filter facts by importance level."""
    filter_data = request.session.get("facts_filter", {})
    # Set to empty string when 0 (All) is selected, otherwise use the value
    filter_data["importance"] = "" if importance_value == 0 else importance_value

    request.session["facts_filter"] = filter_data

    return redirect("case:facts-list")


# =============================================================================
# SEARCH SUBAPP
# =============================================================================


def get_search_data(request, matter):
    """Get search results with filters applied from session."""
    from datetime import datetime

    filter_data = request.session.get("search_filter", {})
    results = []
    query = filter_data.get("query", "").strip()

    if matter and query:
        # Use watson for fuzzy search across all three models
        search_results = watson.search(query)

        for result in search_results:
            obj = result.object
            result_item = None

            # Filter by matter and build result item
            if isinstance(obj, Document) and obj.matter_id == matter.id:
                result_item = {
                    "type": "document",
                    "object": obj,
                    "rank": getattr(result, "watson_rank", 0),
                    "date": obj.date,
                }
            elif isinstance(obj, Highlight) and obj.document.matter_id == matter.id:
                result_item = {
                    "type": "highlight",
                    "object": obj,
                    "rank": getattr(result, "watson_rank", 0),
                    "date": obj.document.date,
                }
            elif isinstance(obj, Fact) and obj.matter_id == matter.id:
                result_item = {
                    "type": "fact",
                    "object": obj,
                    "rank": getattr(result, "watson_rank", 0),
                    "date": obj.date,
                }

            if result_item:
                results.append(result_item)

        # Apply additional filters from session
        result_type = filter_data.get("result_type", "")
        if result_type:
            results = [r for r in results if r["type"] == result_type]

        category = filter_data.get("category", "")
        if category:
            filtered = []
            for r in results:
                if r["type"] == "document" and r["object"].category == category:
                    filtered.append(r)
                elif r["type"] == "highlight":
                    if r["object"].document.category == category:
                        filtered.append(r)
                # Facts don't have category, exclude when filtering by category
            results = filtered

        label_id = filter_data.get("label", "")
        if label_id:
            try:
                label_id = int(label_id)
                results = [
                    r
                    for r in results
                    if hasattr(r["object"], "labels")
                    and r["object"].labels.filter(id=label_id).exists()
                ]
            except (ValueError, TypeError):
                pass

        document_id = filter_data.get("document", "")
        if document_id:
            try:
                document_id = int(document_id)
                filtered = []
                for r in results:
                    if r["type"] == "document" and r["object"].id == document_id:
                        filtered.append(r)
                    elif r["type"] == "highlight":
                        if r["object"].document_id == document_id:
                            filtered.append(r)
                    elif r["type"] == "fact":
                        if r["object"].documents.filter(id=document_id).exists():
                            filtered.append(r)
                results = filtered
            except (ValueError, TypeError):
                pass

        date_from = filter_data.get("date_from", "")
        if date_from:
            try:
                date_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                results = [r for r in results if r["date"] and r["date"] >= date_from]
            except (ValueError, TypeError):
                pass

        date_to = filter_data.get("date_to", "")
        if date_to:
            try:
                date_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                results = [r for r in results if r["date"] and r["date"] <= date_to]
            except (ValueError, TypeError):
                pass

        importance = filter_data.get("importance", "")
        if importance:
            try:
                importance = int(importance)
                results = [r for r in results if r["object"].importance <= importance]
            except (ValueError, TypeError):
                pass

    # Get labels and documents for filter panel
    labels = (
        Label.objects.filter(Q(matter=matter) | Q(matter__isnull=True)).order_by("name")
        if matter
        else []
    )

    documents = (
        Document.objects.filter(matter=matter).order_by("name") if matter else []
    )

    # Create filter object for rendering the form
    filter_obj = SearchFilter(filter_data, matter=matter)

    # Get counts for empty state
    doc_count = Document.objects.filter(matter=matter).count() if matter else 0
    highlight_count = (
        Highlight.objects.filter(document__matter=matter).count() if matter else 0
    )
    fact_count = Fact.objects.filter(matter=matter).count() if matter else 0

    return {
        "results": results,
        "query": query,
        "labels": labels,
        "documents": documents,
        "filter_data": filter_data,
        "filter": filter_obj,
        "doc_count": doc_count,
        "highlight_count": highlight_count,
        "fact_count": fact_count,
    }


@login_required
def search_index(request):
    """Main search view with persistent filter panel."""
    matter, matters = get_selected_matter(request)

    context = {
        "app": "documents",
        "subapp": "search",
        "matter": matter,
        "matters": matters,
    } | get_search_data(request, matter)

    return render(request, "case/search/main.html", context)


@login_required
def search_list(request):
    """HTMX partial for full search content area."""
    matter, matters = get_selected_matter(request)

    context = {
        "app": "documents",
        "subapp": "search",
        "matter": matter,
        "matters": matters,
    } | get_search_data(request, matter)

    return render(request, "case/search/list.html", context)


@login_required
def search_results(request):
    """HTMX partial for search results only."""
    matter, _ = get_selected_matter(request)
    context = get_search_data(request, matter)
    return render(request, "case/search/results.html", context)


@login_required
def search_query(request):
    """Handle search query input via HTMX."""
    matter, _ = get_selected_matter(request)
    filter_data = request.session.get("search_filter", {})

    query = request.POST.get("query", "").strip()
    filter_data["query"] = query
    request.session["search_filter"] = filter_data

    context = get_search_data(request, matter)
    context["is_htmx"] = True
    return render(request, "case/search/results.html", context)


@login_required
def search_filter(request):
    """Filter panel update - POST saves, GET renders panel."""
    matter, _ = get_selected_matter(request)

    if request.method == "POST":
        filter_data = request.session.get("search_filter", {})
        # Update filter data with form values, preserving query
        for key, value in request.POST.items():
            if key != "csrfmiddlewaretoken":
                if value:
                    filter_data[key] = value
                else:
                    filter_data.pop(key, None)
        request.session["search_filter"] = filter_data
        return HttpResponse(status=204, headers={"HX-Trigger": "searchChanged"})

    # GET - render filter panel
    filter_data = request.session.get("search_filter", {})
    filter_obj = SearchFilter(filter_data, matter=matter)

    return render(
        request,
        "case/search/filter-panel.html",
        {"filter": filter_obj, "matter": matter, "filter_data": filter_data},
    )


@login_required
def search_filter_type(request, result_type=None):
    """Quick filter by result type."""
    filter_data = request.session.get("search_filter", {})

    if result_type:
        filter_data["result_type"] = result_type
    else:
        filter_data.pop("result_type", None)

    request.session["search_filter"] = filter_data
    return HttpResponse(status=204, headers={"HX-Trigger": "searchChanged"})


@login_required
def search_clear(request):
    """Clear search query and all filters."""
    request.session["search_filter"] = {}
    return HttpResponse(status=204, headers={"HX-Trigger": "searchChanged"})
