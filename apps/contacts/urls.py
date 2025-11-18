from django.urls import path

from apps.contacts.views import (  # go_to_contact,
    add,
    add_intake,
    assign,
    assign_store,
    delete,
    detail_details,
    detail_intake,
    detail_matters,
    detail_trust,
    edit,
    google_list,
    index,
    remove,
    remove_store,
    select,
    toggle_google_sync,
)

app_name = "contacts"

urlpatterns = [
    path("contacts/", index, name="index"),
    path("contacts/<int:contact_id>", select, name="select"),
    path("contacts/add", add, name="add"),
    path("contacts/<int:id>/edit", edit, name="edit"),
    path("contacts/<int:id>/delete", delete, name="delete"),
    path("contacts/<int:id>/assign", assign, name="assign"),
    path("contacts/<int:id>/assign/store", assign_store, name="assign-store"),
    path("contacts/<int:id>/remove", remove, name="remove"),
    path("contacts/remove/store", remove_store, name="remove-store"),
    path("contacts/<int:id>/add_intake", add_intake, name="add-intake"),
    path(
        "contacts/<int:id>/toggle_google_sync",
        toggle_google_sync,
        name="toggle-google-sync",
    ),
    path("contacts/google_list", google_list, name="google"),
    path("contacts/<int:contact_id>/details", detail_details, name="detail-details"),
    path("contacts/<int:contact_id>/matters", detail_matters, name="detail-matters"),
    path("contacts/<int:contact_id>/trust", detail_trust, name="detail-trust"),
    path("contacts/<int:contact_id>/intake", detail_intake, name="detail-intake"),
]
