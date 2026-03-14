from django.urls import path

# Import all from company.views as company_urls
import apps.settings.checklists.views as checklist_urls
import apps.settings.company.views as company_urls
import apps.settings.contacts.views as contact_urls
import apps.settings.integrations.views as integration_urls
import apps.settings.matters.views as matter_urls
import apps.settings.notifications.views as notification_urls
import apps.settings.profile.views as profile_urls
import apps.settings.session.views as session_urls
import apps.settings.users.views as user_urls

app_name = "settings"

urlpatterns = [
    # Session
    path("settings/", session_urls.index, name="settings"),
    # Integrations
    path("settings/integrations/", integration_urls.index, name="integrations-index"),
    path(
        "settings/google/login/<str:app>",
        integration_urls.google_login,
        name="google-login",
    ),
    path("settings/google/store", integration_urls.google_store, name="google-store"),
    path(
        "settings/google/logout/<str:app>",
        integration_urls.google_logout,
        name="google-logout",
    ),
    # Company
    path("settings/company/", company_urls.company_index, name="company-index"),
    # Users
    path("settings/users/", user_urls.users_index, name="users-index"),
    path("settings/users/list/", user_urls.user_list, name="user-list"),
    path("settings/users/filter/", user_urls.user_filter, name="user-filter"),
    path("settings/users/sort/<str:order>/", user_urls.user_sort, name="user-sort"),
    path(
        "settings/users/change-role/<int:user_id>/<str:role>/",
        user_urls.change_role,
        name="change-role",
    ),
    path(
        "settings/users/switch-status/<int:user_id>/",
        user_urls.switch_status,
        name="switch-status",
    ),
    path(
        "settings/users/edit/<int:user_id>/",
        user_urls.edit_user,
        name="edit-user",
    ),
    path(
        "settings/users/add/",
        user_urls.add_user,
        name="add-user",
    ),
    path(
        "settings/users/toggle-perm/<int:user_id>/<str:perm>/",
        user_urls.toggle_permission,
        name="toggle-perm",
    ),
    path(
        "settings/users/matter-assignments/<int:user_id>/",
        user_urls.matter_assignments,
        name="matter-assignments",
    ),
    path(
        "settings/users/toggle-matter/<int:user_id>/<int:matter_id>/",
        user_urls.toggle_matter_assignment,
        name="toggle-matter-assignment",
    ),
    # Notifications
    path(
        "settings/notifications/",
        notification_urls.notifications_index,
        name="notifications-index",
    ),
    path(
        "settings/notifications/toggle-digest/",
        notification_urls.toggle_digest,
        name="toggle-digest",
    ),
    path(
        "settings/notifications/toggle-weekends/",
        notification_urls.toggle_weekends,
        name="toggle-weekends",
    ),
    path(
        "settings/notifications/send-test/",
        notification_urls.send_test_digest,
        name="send-test-digest",
    ),
    # Profile
    path("settings/profile/", profile_urls.profile_index, name="profile-index"),
    path(
        "settings/profile/personal/",
        profile_urls.personal_profile,
        name="personal-profile",
    ),
    path(
        "settings/profile/personal/<str:form_type>/",
        profile_urls.personal_profile,
        name="personal-profile",
    ),
    # Contacts (Groups and Roles)
    path("settings/contacts/", contact_urls.contacts_index, name="contacts-index"),
    path("settings/contacts/roles/", contact_urls.role_list, name="role-list"),
    path(
        "settings/contacts/roles/filter/<str:status>/",
        contact_urls.role_filter,
        name="role-filter",
    ),
    path("settings/contacts/roles/add/", contact_urls.add_role, name="add-role"),
    path(
        "settings/contacts/roles/edit/<int:role_id>/",
        contact_urls.edit_role,
        name="edit-role",
    ),
    path(
        "settings/contacts/roles/delete/<int:role_id>/",
        contact_urls.delete_role,
        name="delete-role",
    ),
    path("settings/contacts/groups/", contact_urls.group_list, name="group-list"),
    path(
        "settings/contacts/groups/filter/<str:status>/",
        contact_urls.group_filter,
        name="group-filter",
    ),
    path("settings/contacts/groups/add/", contact_urls.add_group, name="add-group"),
    path(
        "settings/contacts/groups/edit/<int:group_id>/",
        contact_urls.edit_group,
        name="edit-group",
    ),
    path(
        "settings/contacts/groups/delete/<int:group_id>/",
        contact_urls.delete_group,
        name="delete-group",
    ),
    path(
        "settings/contacts/groups/update-order/",
        contact_urls.update_group_order,
        name="update-group-order",
    ),
    # Checklists
    path(
        "settings/checklists/",
        checklist_urls.checklists_index,
        name="checklists-index",
    ),
    path(
        "settings/checklists/list/",
        checklist_urls.checklists_list,
        name="checklists-list",
    ),
    path(
        "settings/checklists/table/",
        checklist_urls.checklists_table,
        name="checklists-table",
    ),
    path(
        "settings/checklists/order-by/<str:order>/",
        checklist_urls.checklists_order_by,
        name="checklists-order-by",
    ),
    path(
        "settings/checklists/filter/keyword/",
        checklist_urls.checklists_filter_keyword,
        name="checklists-filter-keyword",
    ),
    path(
        "settings/checklists/add/",
        checklist_urls.add_checklist_template,
        name="add-checklist-template",
    ),
    path(
        "settings/checklists/<int:template_id>/edit/",
        checklist_urls.edit_checklist_template,
        name="edit-checklist-template",
    ),
    path(
        "settings/checklists/<int:template_id>/delete/",
        checklist_urls.delete_checklist_template,
        name="delete-checklist-template",
    ),
    path(
        "settings/checklists/<int:template_id>/move/",
        checklist_urls.checklist_template_move,
        name="checklist-template-move",
    ),
    path(
        "settings/checklists/<int:template_id>/items/add/",
        checklist_urls.add_template_item,
        name="add-template-item",
    ),
    path(
        "settings/checklists/items/<int:item_id>/delete/",
        checklist_urls.delete_template_item,
        name="delete-template-item",
    ),
    path(
        "settings/checklists/<int:template_id>/items/reorder/",
        checklist_urls.reorder_template_items,
        name="reorder-template-items",
    ),
    # Checklist folders
    path(
        "settings/checklists/folders/select/<int:folder_id>/",
        checklist_urls.checklist_folder_select,
        name="checklist-folder-select",
    ),
    path(
        "settings/checklists/folders/unsorted/",
        checklist_urls.checklist_folder_unsorted,
        name="checklist-folder-unsorted",
    ),
    path(
        "settings/checklists/folders/all/",
        checklist_urls.checklist_folder_all,
        name="checklist-folder-all",
    ),
    path(
        "settings/checklists/folders/add/",
        checklist_urls.checklist_folder_add,
        name="checklist-folder-add",
    ),
    path(
        "settings/checklists/folders/edit/<int:folder_id>",
        checklist_urls.checklist_folder_edit,
        name="checklist-folder-edit",
    ),
    path(
        "settings/checklists/folders/delete/<int:folder_id>/confirm",
        checklist_urls.checklist_folder_delete_confirm,
        name="checklist-folder-delete-confirm",
    ),
    path(
        "settings/checklists/folders/delete/<int:folder_id>",
        checklist_urls.checklist_folder_delete,
        name="checklist-folder-delete",
    ),
    path(
        "settings/checklists/folders/move/<int:folder_id>/",
        checklist_urls.checklist_folder_move,
        name="checklist-folder-move",
    ),
    path(
        "settings/checklists/folders/toggle/<int:folder_id>/",
        checklist_urls.checklist_folder_toggle_expand,
        name="checklist-folder-toggle",
    ),
    path(
        "settings/checklists/folders/toggle-all/",
        checklist_urls.checklist_folder_toggle_all,
        name="checklist-folder-toggle-all",
    ),
    # Checklist multi-select
    path(
        "settings/checklists/toggle-select/<int:template_id>/",
        checklist_urls.checklists_toggle_select,
        name="checklists-toggle-select",
    ),
    path(
        "settings/checklists/select-all/",
        checklist_urls.checklists_select_all,
        name="checklists-select-all",
    ),
    path(
        "settings/checklists/clear-selection/",
        checklist_urls.checklists_clear_selection,
        name="checklists-clear-selection",
    ),
    path(
        "settings/checklists/bulk-move/",
        checklist_urls.checklists_bulk_move,
        name="checklists-bulk-move",
    ),
    path(
        "settings/checklists/bulk-delete/",
        checklist_urls.checklists_bulk_delete,
        name="checklists-bulk-delete",
    ),
    # Matters (Practice Areas)
    path("settings/matters/", matter_urls.matters_index, name="matters-index"),
    path(
        "settings/matters/practice-areas/",
        matter_urls.practice_area_list,
        name="practice-area-list",
    ),
    path(
        "settings/matters/practice-areas/filter/<str:status>/",
        matter_urls.practice_area_filter,
        name="practice-area-filter",
    ),
    path(
        "settings/matters/practice-areas/add/",
        matter_urls.add_practice_area,
        name="add-practice-area",
    ),
    path(
        "settings/matters/practice-areas/edit/<int:practice_area_id>/",
        matter_urls.edit_practice_area,
        name="edit-practice-area",
    ),
    path(
        "settings/matters/practice-areas/delete/<int:practice_area_id>/",
        matter_urls.delete_practice_area,
        name="delete-practice-area",
    ),
]
