from apps.billing.credits.filters import CreditsFilter
from apps.billing.credits.models import Credit
from apps.management.pagination import CustomPaginator


def get_credits_data(request):
    filter_data = request.session.get("credits_filter", {})

    if filter_data:
        filter = CreditsFilter(filter_data)
        credits = filter.qs
        pass
    else:
        credits = Credit.objects.all().select_related("matter").order_by("-date", "-id")

    pagination = CustomPaginator(
        credits, per_page=10, request=request, session_key="credits_pagination"
    )

    context = {
        "pagination": pagination,
        "session_key": "credits_pagination",
        "trigger_key": "creditsChanged",
        "objects": pagination.get_object_list(),
    }

    return context
