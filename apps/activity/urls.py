from django.urls import path

from apps.activity.views_expenses import (
    add_expense,
    delete_expense,
    edit_expense,
    filter_expenses,
    list_expenses,
    quick_filter_expenses,
    toggle_entered_expenses,
)
from apps.activity.views_time import (
    add_time,
    delete_time,
    edit_time,
    export,
    filter_time,
    list_time,
    quick_filter_time,
    quick_filter_time_matter,
    toggle_entered_time,
)

app_name = "activity"

urlpatterns = [
    path("activity/", list_time, name="list-time"),
    path("activity/add-time", add_time, name="add-time"),
    path("activity/add-time/<int:id>", add_time, name="add-time"),
    path("activity/<int:id>/edit-time", edit_time, name="edit-time"),
    path("activity/<int:id>/delete-time", delete_time, name="delete-time"),
    path(
        "activity/<int:id>/toggle-entered-time",
        toggle_entered_time,
        name="toggle-entered-time",
    ),
    path("activity/filter-time", filter_time, name="filter-time"),
    path(
        "activity/quick-filter-time/<str:quick_filter>",
        quick_filter_time,
        name="quick-filter-time",
    ),
    path(
        "activity/quick-filter-time-matter/<int:matter_id>",
        quick_filter_time_matter,
        name="quick-filter-time-matter",
    ),
    path("activity/export", export, name="export"),
    path("activity/expenses", list_expenses, name="list-expenses"),
    path("activity/add-expense", add_expense, name="add-expense"),
    path(
        "activity/add-expense/<int:id>",
        add_expense,
        name="add-expense",
    ),
    path(
        "activity/<int:id>/edit-expense",
        edit_expense,
        name="edit-expense",
    ),
    path(
        "activity/<int:id>/delete-expense",
        delete_expense,
        name="delete-expense",
    ),
    path(
        "activity/<int:id>/toggle-entered-expense",
        toggle_entered_expenses,
        name="toggle-entered-expense",
    ),
    path(
        "activity/quick-filter-expense/<str:tab>",
        quick_filter_expenses,
        name="quick-filter-expense",
    ),
    path(
        "activity/filter-expenses/",
        filter_expenses,
        name="filter-expenses",
    ),
]
