from django import forms

from apps.matters.models import Group, Role
from config.settings import CustomFormRendererCompact


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ["name", "is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "is_active"]

        ACTIVE_CHOICES = (
            (True, "Active"),
            (False, "Inactive"),
        )

        widgets = {
            "is_active": forms.Select(choices=ACTIVE_CHOICES),
        }

        labels = {
            "is_active": "Status",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
