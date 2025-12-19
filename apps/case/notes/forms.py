from django import forms

from apps.notes.models import Note
from config.settings import CustomFormRendererCompact


class NoteForm(forms.ModelForm):
    default_renderer = CustomFormRendererCompact

    class Meta:
        model = Note
        fields = ["category", "title"]
        widgets = {
            "title": forms.TextInput(attrs={"autofocus": True, "class": "span2"}),
            "category": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("matter", None)
        super().__init__(*args, **kwargs)
