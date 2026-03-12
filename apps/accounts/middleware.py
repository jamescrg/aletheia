from django.http import HttpResponseForbidden


class PermissionMiddleware:
    """Block paths based on user permissions for non-admin users."""

    PERMISSION_PATHS = [
        ("/invoicing/", "perm_financial"),
        ("/intakes/", "perm_intakes"),
        ("/reports/", "perm_reports"),
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_admin:
            if request.path.startswith("/admin/"):
                return HttpResponseForbidden()

            for path_prefix, perm_field in self.PERMISSION_PATHS:
                if request.path.startswith(path_prefix) and not getattr(
                    request.user, perm_field
                ):
                    return HttpResponseForbidden()

        return self.get_response(request)
