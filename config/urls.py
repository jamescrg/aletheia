from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import path, include

from apps.activity import views as activity
from apps.contacts import views as contacts
from apps.events import views as events
from apps.invoicing import views as invoicing
from apps.lab import views as lab
from apps.search import views as search
from apps.settings import views as settings
from apps.trust import views as trust

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Accounts App
    path("accounts/", include("apps.accounts.urls")),
    # Folders App
    path("", include("apps.folders.urls")),
    # Agenda App
    path("", include("apps.agenda.urls")),
    # Intakes App
    path("", include("apps.intakes.urls")),
    # Matters App
    path("", include("apps.matters.urls")),
    # --------------------------------------
    # contacts
    # --------------------------------------
    path("contacts/", contacts.index, name="contacts"),
    path("contacts/<int:id>", contacts.select, name="contacts-select"),
    path("contacts/add", contacts.add, name="contacts-add"),
    path("contacts/<int:id>/edit", contacts.edit, name="contacts-edit"),
    path("contacts/<int:id>/delete", contacts.delete, name="contacts-delete"),
    path("contacts/<int:id>/assign", contacts.assign, name="contacts-assign"),
    path(
        "contacts/<int:id>/assign/store",
        contacts.assign_store,
        name="contacts-assign-store",
    ),
    path("contacts/<int:id>/remove", contacts.remove, name="contacts-remove"),
    path(
        "contacts/<int:id>/remove/store",
        contacts.remove_store,
        name="contacts-remove-store",
    ),
    path(
        "contacts/<int:id>/add_intake", contacts.add_intake, name="contacts-add-intake"
    ),
    path(
        "contacts/<int:id>/toggle_google_sync",
        contacts.toggle_google_sync,
        name="contacts-toggle-google-sync",
    ),
    path("contacts/google_list", contacts.google_list, name="contacts-google"),
    # --------------------------------------
    # events
    # --------------------------------------
    path("events/", events.index, name="events"),
    path("events/add", events.add, name="events-add"),
    path("events/add/<str:origin>", events.add, name="events-add-origin"),
    path(
        "events/deadline-results",
        events.deadline_results,
        name="events-deadline-results",
    ),
    path("events/add/<int:matter_id>", events.add, name="events-add-matter"),
    path(
        "events/add/<int:matter_id>/<str:origin>",
        events.add,
        name="events-add-matter-origin",
    ),
    path("events/<int:id>/edit", events.edit, name="events-edit"),
    path("events/<int:id>/edit/<str:origin>", events.edit, name="events-edit-origin"),
    path("events/<int:id>/delete", events.delete, name="events-delete"),
    path(
        "events/<int:id>/delete/<str:origin>",
        events.delete,
        name="events-delete-origin",
    ),
    # --------------------------------------
    # activity
    # --------------------------------------
    path("activity/", activity.index, name="activity-list"),
    path("activity/add", activity.add, name="activity-add"),
    path("activity/add_expense", activity.add_expense, name="activity-add-expense"),
    path("activity/add/<int:id>", activity.add, name="activity-add"),
    path(
        "activity/add_expense/<int:id>",
        activity.add_expense,
        name="activity-add-expense",
    ),
    path("activity/<int:id>/edit", activity.edit, name="activity-edit"),
    path(
        "activity/<int:id>/edit_expense",
        activity.edit_expense,
        name="activity-edit-expense",
    ),
    path("activity/<int:id>/delete", activity.delete, name="activity-delete"),
    path(
        "activity/<int:id>/delete_expense",
        activity.delete_expense,
        name="activity-delete-expense",
    ),
    path(
        "activity/<int:id>/toggle-entered",
        activity.toggle_entered,
        name="activity-toggle-entered",
    ),
    path(
        "activity/<int:id>/toggle-entered-expense",
        activity.toggle_entered_expense,
        name="activity-toggle-entered-expense",
    ),
    path("activity/filter", activity.filter, name="activity-filter"),
    path(
        "activity/filter/update", activity.filter_update, name="activity-filter-update"
    ),
    path(
        "activity/filter/<str:quick_filter>",
        activity.filter_quick,
        name="activity-filter-quick",
    ),
    path(
        "activity/filter/matter/<int:id>",
        activity.filter_matter,
        name="activity-filter-matter",
    ),
    path("activity/export", activity.export, name="activity-export"),
    # --------------------------------------
    # trust
    # --------------------------------------
    path("trust/", trust.index, name="trust"),
    path("trust/history/", trust.history, name="trust-history"),
    path("trust/history/<str:interval>/", trust.history, name="trust-history-interval"),
    path("trust/client/<int:id>", trust.client, name="trust-client"),
    path("trust/<int:contact_id>/add", trust.add, name="trust-add"),
    path("trust/<int:id>/edit", trust.edit, name="trust-edit"),
    path("trust/<int:id>/delete", trust.delete, name="trust-delete"),
    path("trust/<int:id>/entered", trust.toggle_entered, name="trust-entered"),
    path("trust/<int:id>/confirmed", trust.toggle_confirmed, name="trust-confirmed"),
    # --------------------------------------
    # search
    # --------------------------------------
    path("search/", search.index, name="search"),
    path("search/results", search.results, name="search-results"),
    # --------------------------------------
    # settings
    # --------------------------------------
    path("settings/", settings.index, name="settings"),
    path(
        "settings/google/login/<str:app>",
        settings.google_login,
        name="settings-google-login",
    ),
    path("settings/google/store", settings.google_store, name="settings-google-store"),
    path(
        "settings/google/logout/<str:app>",
        settings.google_logout,
        name="settings-google-logout",
    ),
    # --------------------------------------
    # invoicing
    # --------------------------------------
    path("invoicing/", invoicing.index, name="invoicing"),
    # --------------------------------------
    # lab
    # --------------------------------------
    path("lab/", lab.index, name="lab"),
    path("lab/results", lab.results, name="lab-results"),
    path("lab/email", lab.email_test, name="email-test"),
]

urlpatterns += staticfiles_urlpatterns()
