from django.urls import path

from apps.checklists import views

app_name = "checklists"

urlpatterns = [
    # Page views
    path("checklists/", views.checklists_index, name="index"),
    path("checklists/list/", views.checklists_list, name="list"),
    path("checklists/table/", views.checklists_table, name="table"),
    # Sort and filter
    path(
        "checklists/order-by/<str:order>/", views.checklists_order_by, name="order-by"
    ),
    path(
        "checklists/filter/keyword/",
        views.checklists_filter_keyword,
        name="filter-keyword",
    ),
    # Template CRUD
    path(
        "checklists/add/", views.add_checklist_template, name="add-checklist-template"
    ),
    path(
        "checklists/<int:template_id>/edit/",
        views.edit_checklist_template,
        name="edit-checklist-template",
    ),
    path(
        "checklists/<int:template_id>/delete/",
        views.delete_checklist_template,
        name="delete-checklist-template",
    ),
    path(
        "checklists/<int:template_id>/move/",
        views.checklist_template_move,
        name="template-move",
    ),
    # Template items
    path(
        "checklists/<int:template_id>/items/add/",
        views.add_template_item,
        name="add-template-item",
    ),
    path(
        "checklists/items/<int:item_id>/delete/",
        views.delete_template_item,
        name="delete-template-item",
    ),
    path(
        "checklists/<int:template_id>/items/reorder/",
        views.reorder_template_items,
        name="reorder-template-items",
    ),
    # Folders
    path(
        "checklists/folders/select/<int:folder_id>/",
        views.checklist_folder_select,
        name="folder-select",
    ),
    path(
        "checklists/folders/unsorted/",
        views.checklist_folder_unsorted,
        name="folder-unsorted",
    ),
    path("checklists/folders/all/", views.checklist_folder_all, name="folder-all"),
    path("checklists/folders/add/", views.checklist_folder_add, name="folder-add"),
    path(
        "checklists/folders/edit/<int:folder_id>",
        views.checklist_folder_edit,
        name="folder-edit",
    ),
    path(
        "checklists/folders/delete/<int:folder_id>/confirm",
        views.checklist_folder_delete_confirm,
        name="folder-delete-confirm",
    ),
    path(
        "checklists/folders/delete/<int:folder_id>",
        views.checklist_folder_delete,
        name="folder-delete",
    ),
    path(
        "checklists/folders/move/<int:folder_id>/",
        views.checklist_folder_move,
        name="folder-move",
    ),
    path(
        "checklists/folders/toggle/<int:folder_id>/",
        views.checklist_folder_toggle_expand,
        name="folder-toggle",
    ),
    path(
        "checklists/folders/toggle-all/",
        views.checklist_folder_toggle_all,
        name="folder-toggle-all",
    ),
    # Multi-select
    path(
        "checklists/toggle-select/<int:template_id>/",
        views.checklists_toggle_select,
        name="toggle-select",
    ),
    path("checklists/select-all/", views.checklists_select_all, name="select-all"),
    path(
        "checklists/clear-selection/",
        views.checklists_clear_selection,
        name="clear-selection",
    ),
    path("checklists/bulk-move/", views.checklists_bulk_move, name="bulk-move"),
    path("checklists/bulk-delete/", views.checklists_bulk_delete, name="bulk-delete"),
    # Task integration
    path(
        "checklists/<int:task_id>/modal/", views.checklist_modal, name="checklist-modal"
    ),
    path(
        "checklists/<int:task_id>/attach/",
        views.attach_checklist,
        name="attach-checklist",
    ),
    path(
        "checklists/item/<int:item_id>/toggle/",
        views.toggle_checklist_item,
        name="toggle-checklist-item",
    ),
    path(
        "checklists/<int:task_id>/remove/",
        views.remove_checklist,
        name="remove-checklist",
    ),
    path(
        "checklists/<int:task_id>/refresh/",
        views.refresh_checklist,
        name="refresh-checklist",
    ),
]
