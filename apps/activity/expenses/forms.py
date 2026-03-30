from django import forms

from apps.accounts.access import filter_matters_for_user
from config.settings import CustomFormRendererCompact

from .models import ExpenseEntry


class ExpenseEntryForm(forms.ModelForm):
    class Meta:
        model = ExpenseEntry

        fields = (
            "matter",
            "date",
            "description",
            "amount",
            "category",
            "comp",
            "entered",
        )

        CATEGORY_CHOICES = (
            (None, "----------"),
            ("Contract Services", "Contract Services"),
            ("Court Reporters", "Court Reporters"),
            ("Filing Fee", "Filing Fee"),
            ("Outside Counsel", "Outside Counsel"),
            ("Postage", "Postage"),
            ("Process Server", "Process Server"),
        )

        COMP_CHOICES = (
            (0, "No"),
            (1, "Yes"),
        )

        ENTERED_CHOICES = (
            (0, "No"),
            (1, "Yes"),
        )

        widgets = {
            "matter": forms.Select(attrs={"onchange": "updateRate()"}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(
                attrs={
                    "onfocus": "moveFocusToEnd(this)",
                    "rows": "3",
                    "class": "span2",
                }
            ),
            "comp": forms.Select(choices=COMP_CHOICES),
            "entered": forms.Select(choices=ENTERED_CHOICES),
            "category": forms.Select(choices=CATEGORY_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
        if user:
            self.fields["matter"].queryset = filter_matters_for_user(
                self.fields["matter"].queryset, user
            )
