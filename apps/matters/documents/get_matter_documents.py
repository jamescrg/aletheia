from apps.documents.filters import DocumentsFilter
from apps.documents.models import Document


def get_matter_documents(request, matter):
    filter_data = request.session.get("matters_documents_filter")

    if filter_data:
        filter = DocumentsFilter(filter_data)
        documents = filter.qs
    else:
        documents = (
            Document.objects.filter(matter=matter)
            .select_related("matter", "uploaded_by")
            .order_by("-uploaded_at")
        )

    return {"documents": documents}
