from django.shortcuts import get_object_or_404

from apps.folders.models import Folder


def get_list_data(request):
    folders = Folder.objects.filter(app="contacts").order_by("name")
    folders = list(folders)
    folders.append({"id": "unsorted", "name": "Unsorted"})

    client_folders = [
        {"id": "clients", "name": "Clients"},
        {"id": "former", "name": "Former Clients"},
    ]

    if request.session.get("contacts_selected_folder_id"):
        selected_folder_id = request.session["contacts_selected_folder_id"]
        selected_folder = get_object_or_404(Folder, pk=selected_folder_id)
    else:
        selected_folder = None

    context = {
        "app": "contacts",
        "folders": folders,
        "selected_folder": selected_folder,
        "client_folders": client_folders,
    }

    return context
