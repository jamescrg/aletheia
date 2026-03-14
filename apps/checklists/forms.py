from django import forms

from apps.checklists.models import ChecklistFolder, ChecklistTemplate
from config.settings import CustomFormRendererCompact


class ChecklistTemplateForm(forms.ModelForm):
    class Meta:
        model = ChecklistTemplate
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()


class ChecklistFolderForm(forms.ModelForm):
    class Meta:
        model = ChecklistFolder
        fields = ["name", "parent"]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Folder name",
                    "autofocus": True,
                    "onfocus": "moveFocusToEnd(this)",
                }
            ),
            "parent": forms.Select(attrs={"class": "form-control"}),
        }

        labels = {
            "name": "Folder Name",
            "parent": "Parent Folder",
        }

    def __init__(self, *args, exclude_folder=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["parent"].required = False
        self.fields["parent"].empty_label = "— None (root level) —"

        qs = ChecklistFolder.objects.filter(depth__lt=3).order_by("name")
        if exclude_folder and exclude_folder.pk:
            descendant_ids = [d.pk for d in exclude_folder.get_descendants()]
            exclude_ids = [exclude_folder.pk] + descendant_ids
            qs = qs.exclude(pk__in=exclude_ids)
        self.fields["parent"].queryset = qs

        choices = [("", self.fields["parent"].empty_label)]
        for folder in qs:
            indent = "\u00a0\u00a0\u00a0\u00a0" * folder.depth
            choices.append((folder.pk, f"{indent}{folder.name}"))
        self.fields["parent"].choices = choices


class ChecklistFolderMoveForm(forms.Form):
    destination = forms.ModelChoiceField(
        queryset=ChecklistFolder.objects.none(),
        required=False,
        empty_label="Root level",
        widget=forms.RadioSelect,
    )
