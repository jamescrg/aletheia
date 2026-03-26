from django import forms

from apps.case.models import Fact
from config.settings import CustomFormRendererCompact

IMPORTANCE_CHOICES = (
    (5, "Highest"),
    (4, "High"),
    (3, "Normal"),
    (2, "Low"),
    (1, "Lowest"),
)


class FactForm(forms.ModelForm):
    class Meta:
        model = Fact

        fields = (
            "date",
            "time",
            "description",
            "color",
            "importance",
        )

        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "time": forms.TimeInput(
                attrs={"type": "time", "tabindex": "5"}, format="%H:%M"
            ),
            "description": forms.Textarea(
                attrs={
                    "onfocus": "moveFocusToEnd(this)",
                    "class": "span2",
                    "rows": 3,
                }
            ),
            "color": forms.Select(),
            "importance": forms.Select(choices=IMPORTANCE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        # Remove matter kwarg if passed (no longer needed)
        kwargs.pop("matter", None)
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
