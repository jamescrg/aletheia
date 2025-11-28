import pytest
from pytest_django.asserts import assertTemplateUsed

from apps.matters.models import Relationship

pytestmark = pytest.mark.django_db


def test_assign(client, matter):
    response = client.get(f"/matters/{matter.id}/contacts/assign")
    assert response.status_code == 200
    assertTemplateUsed(response, "matters/contacts/assign-modal.html")
    # Check that groups and roles are passed in context
    assert "groups" in response.context
    assert "roles" in response.context


def test_assign_results(client, matter, contact):
    data = {"search_text": "Gandhi"}
    response = client.post(f"/matters/{matter.id}/contacts/assign/results", data)
    assert response.status_code == 200
    assertTemplateUsed(response, "matters/contacts/results.html")
    assert response.context["contacts"]


def test_assign_store(client, matter, contact, role, group):
    data = {
        "matter_id": matter.id,
        "contact_id": contact.id,
        "role_id": role.id,
        "group_id": group.id,
    }
    response = client.post("/matters/assign/store", data)
    assert response.status_code == 204
    found = Relationship.objects.filter(matter=matter).first()
    assert found


def test_assign_edit(client, relationship):
    response = client.get(f"/matters/assign/{relationship.id}/edit")
    assert response.status_code == 200
    assertTemplateUsed(response, "matters/contacts/assign-role-modal.html")


def test_assign_update(client, relationship, role, group):
    data = {"role_id": role.id, "group_id": group.id}
    response = client.post(f"/matters/assign/{relationship.id}/update", data)
    assert response.status_code == 204
    found = Relationship.objects.filter(role_id=role.id).first()
    assert found


def test_delete(client, relationship):
    response = client.post(f"/matters/assign/{relationship.id}/delete")
    assert response.status_code == 204
    found = Relationship.objects.filter(pk=relationship.id).exists()
    assert not found


def test_filter_group(client, matter, group):
    """Test that filter_group sets session filter and returns 204."""
    response = client.post(f"/matters/{matter.id}/contacts/filter/group/{group.id}/")
    assert response.status_code == 204
    assert response.headers.get("HX-Trigger") == "contactsReload"
    # Verify session was set
    session = client.session
    session_key = f"matter_contacts_filter_{matter.id}"
    assert session.get(session_key, {}).get("group") == group.id


def test_filter_group_clear(client, matter):
    """Test that filter_group with 0 clears the filter."""
    response = client.post(f"/matters/{matter.id}/contacts/filter/group/0/")
    assert response.status_code == 204
    session = client.session
    session_key = f"matter_contacts_filter_{matter.id}"
    assert session.get(session_key, {}).get("group") == ""


def test_filter_role(client, matter, role):
    """Test that filter_role sets session filter and returns 204."""
    response = client.post(f"/matters/{matter.id}/contacts/filter/role/{role.id}/")
    assert response.status_code == 204
    assert response.headers.get("HX-Trigger") == "contactsReload"
    # Verify session was set
    session = client.session
    session_key = f"matter_contacts_filter_{matter.id}"
    assert session.get(session_key, {}).get("role") == role.id


def test_filter_role_clear(client, matter):
    """Test that filter_role with 0 clears the filter."""
    response = client.post(f"/matters/{matter.id}/contacts/filter/role/0/")
    assert response.status_code == 204
    session = client.session
    session_key = f"matter_contacts_filter_{matter.id}"
    assert session.get(session_key, {}).get("role") == ""
