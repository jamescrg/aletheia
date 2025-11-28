from datetime import date

import pytest
from django.test import Client

from apps.accounts.models import CustomUser


@pytest.fixture
def user():
    user = CustomUser.objects.create(
        username="testuser", email="test@example.com", user_rate=100
    )
    user.set_password("testpass123")
    user.save()
    return user


@pytest.fixture
def authenticated_client(user):
    client = Client()
    client.login(username="testuser", password="testpass123")
    return client


@pytest.fixture
def unauthenticated_client():
    return Client()


@pytest.mark.django_db
class TestDailyDashCheckMiddleware:
    def test_unauthenticated_user_not_redirected(self, unauthenticated_client):
        """Unauthenticated users should not be redirected to dash."""
        response = unauthenticated_client.get("/accounts/login/")
        assert response.status_code == 200

    def test_first_request_redirects_to_dash(self, authenticated_client):
        """First request of the day should redirect to dash."""
        # Try to access events page (not dash)
        response = authenticated_client.get("/events/", follow=False)

        # Should redirect to dash
        assert response.status_code == 302
        assert response.url == "/dash/"

    def test_dash_page_sets_session(self, authenticated_client):
        """Visiting dash page should set the session key."""
        response = authenticated_client.get("/dash/")

        assert response.status_code == 200
        assert (
            authenticated_client.session.get("daily_dash_check_date")
            == date.today().isoformat()
        )

    def test_after_dash_other_pages_accessible(self, authenticated_client):
        """After viewing dash, other pages should be accessible."""
        # First visit dash to set the session
        authenticated_client.get("/dash/")

        # Now events page should work without redirect
        response = authenticated_client.get("/events/", follow=False)
        assert response.status_code == 200

    def test_htmx_requests_not_redirected(self, authenticated_client):
        """HTMX requests should not be redirected."""
        response = authenticated_client.get(
            "/events/",
            HTTP_HX_REQUEST="true",
        )
        # HTMX requests bypass the redirect
        assert response.status_code == 200

    def test_ajax_requests_not_redirected(self, authenticated_client):
        """AJAX requests should not be redirected."""
        response = authenticated_client.get(
            "/events/",
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        # AJAX requests bypass the redirect
        assert response.status_code == 200

    def test_exempt_paths_not_redirected(self, authenticated_client):
        """Exempt paths like /accounts/ should not be redirected."""
        response = authenticated_client.get("/accounts/login/", follow=False)
        # Should not be a redirect to dash (login page doesn't redirect to dash)
        assert response.status_code != 302 or response.url != "/dash/"

    def test_2fa_verify_page_not_redirected(self, unauthenticated_client, user):
        """The 2FA verification page should not be redirected to dash."""
        # Simulate having gone through step 1 of login
        session = unauthenticated_client.session
        session["pending_user_id"] = user.id
        session.save()

        response = unauthenticated_client.get("/accounts/login/verify/", follow=False)
        # Should not redirect to dash - user is not authenticated yet
        assert response.status_code == 200
