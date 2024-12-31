from django.shortcuts import get_object_or_404

from apps.folders.models import Folder

SPECIAL_FOLDERS = ["clients", "former", "unsorted", "add", "insert", "edit"]

CLIENT_FOLDERS = [
    {"id": "clients", "name": "Clients"},
    {"id": "former", "name": "Former Clients"},
]


def get_list_data(request):
    folders = Folder.objects.filter(app="contacts").order_by("name")
    folders = list(folders)
    folders.append({"id": "unsorted", "name": "Unsorted"})

    con_selected_folder_id = request.session.get("contacts_selected_folder_id")

    if con_selected_folder_id and con_selected_folder_id not in SPECIAL_FOLDERS:
        selected_folder_id = request.session["contacts_selected_folder_id"]

        selected_folder = get_object_or_404(Folder, pk=selected_folder_id)
    else:
        selected_folder = None

    context = {
        "app": "contacts",
        "folders": folders,
        "selected_folder": selected_folder,
        "client_folders": CLIENT_FOLDERS,
    }

    return context
