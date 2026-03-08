from django.urls import path

from apps.dash.views import dash_index

app_name = "dash"

urlpatterns = [
    path("dash/", dash_index, name="index"),
]
