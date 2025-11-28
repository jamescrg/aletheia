from datetime import date

from django.shortcuts import redirect
from django.urls import reverse


class DailyDashCheckMiddleware:
    """
    Middleware that ensures users view the agenda dashboard at least once per day.

    On the first request of each day, redirects authenticated users to the
    agenda dash page. The dash view marks the check-in as complete.
    """

    # URLs that should be exempt from the redirect
    EXEMPT_PATHS = [
        "/accounts/",  # Login/logout pages
        "/static/",  # Static files
        "/media/",  # Media files
        "/__debug__/",  # Debug toolbar
    ]

    SESSION_KEY = "daily_dash_check_date"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for unauthenticated users
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Skip for exempt paths
        if self._is_exempt_path(request.path):
            return self.get_response(request)

        # Skip for AJAX/HTMX requests (don't interrupt partial page updates)
        if (
            request.headers.get("HX-Request")
            or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        ):
            return self.get_response(request)

        # Check if user has already viewed dash today
        today = date.today().isoformat()
        last_check_date = request.session.get(self.SESSION_KEY)

        # Get the dash URL
        dash_url = reverse("agenda:dash-index")

        # If already on dash page, mark as checked and continue
        if request.path == dash_url:
            request.session[self.SESSION_KEY] = today
            return self.get_response(request)

        # If not checked in today, redirect to dash
        if last_check_date != today:
            return redirect(dash_url)

        return self.get_response(request)

    def _is_exempt_path(self, path):
        """Check if the path should be exempt from the daily check."""
        return any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)
