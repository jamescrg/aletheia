from django.urls import path

from apps.folders.views import delete, edit, insert, select, update

app_name = "folders"

urlpatterns = [
    path("folders/<int:id>/<str:app>/<str:action_type>", select, name="list"),
    path("folders/insert/<str:app>/<str:action_type>", insert, name="insert"),
    path("folders/edit/<int:folder_id>", edit, name="edit"),
    path("folders/update/<int:folder_id>", update, name="update"),
    path("folders/delete/<int:folder_id>/<str:app>", delete, name="delete"),
]
