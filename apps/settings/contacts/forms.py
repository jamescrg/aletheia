from django import forms

from apps.matters.models import Group, Role
from config.settings import CustomFormRendererCompact


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ["name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ["name", "order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
