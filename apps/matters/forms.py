from django import forms

from apps.accounts.models import CustomUser
from config.settings import CustomFormRendererCompact

from .models import Matter, PracticeArea


class MatterForm(forms.ModelForm):
    class Meta:
        model = Matter

        fields = (
            "status",
            "date_start",
            "client",
            "name",
            "description",
            "work_status",
            "practice_area",
            "jurisdiction",
            "members",
        )

        STATUSES = (
            ("Pending", "Pending"),
            ("Open", "Open"),
            ("Complete", "Complete"),
            ("Closed", "Closed"),
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "autofocus": "autofocus",
                    "onfocus": "moveFocusToEnd(this)",
                    "class": "span2",
                }
            ),
            "description": forms.TextInput(
                attrs={
                    "class": "span2",
                }
            ),
            "work_status": forms.TextInput(
                attrs={
                    "class": "span2",
                }
            ),
            "status": forms.Select(
                choices=STATUSES,
            ),
            "client": forms.Select(
                attrs={
                    "class": "span2",
                }
            ),
            "date_start": forms.DateInput(attrs={"type": "date"}),
            "jurisdiction": forms.TextInput(
                attrs={
                    "class": "span2",
                }
            ),
        }

        labels = {
            "date_start": "Open Date",
            "clio_matter_id": "Clio Matter",
            "client_reference_id": "Client Reference",
            "practice_area": "Practice Area",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()

        # Filter practice areas to only show active ones
        self.fields["practice_area"].queryset = PracticeArea.objects.filter(
            is_active=True
        )

        # Members field — only show users with limited matter access
        limited_users = CustomUser.objects.filter(
            perm_all_matters=False, is_active=True
        )
        if limited_users.exists():
            self.fields["members"].queryset = limited_users
            self.fields["members"].widget = forms.CheckboxSelectMultiple()
            self.fields["members"].required = False
            self.fields["members"].label = "Assigned Users"
        else:
            del self.fields["members"]
