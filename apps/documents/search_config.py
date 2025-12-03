"""Watson search registration for Documents app models."""

from watson import search as watson

from apps.documents.models import Document, Fact, Highlight

# Register Document model for search
watson.register(
    Document,
    fields=("name", "description", "ocr_text"),
)

# Register Highlight model for search
watson.register(
    Highlight,
    fields=("slug", "text"),
)

# Register Fact model for search
watson.register(
    Fact,
    fields=("description",),
)
