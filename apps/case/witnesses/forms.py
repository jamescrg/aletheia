from django import forms
from django.core.exceptions import ValidationError

from apps.case.models import Witness
from config.helpers import normalize_phone
from config.settings import CustomFormRendererCompact

IMPORTANCE_CHOICES = (
    (7, "Highest"),
    (6, "Higher"),
    (5, "High"),
    (4, "Normal"),
    (3, "Low"),
    (2, "Lower"),
    (1, "Lowest"),
)


class WitnessForm(forms.ModelForm):
    class Meta:
        model = Witness

        fields = (
            "name",
            "affiliation",
            "phone",
            "email",
            "address",
            "knowledge",
            "alignment",
            "importance",
        )

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "span2",
                }
            ),
            "affiliation": forms.TextInput(),
            "phone": forms.TextInput(),
            "email": forms.EmailInput(),
            "address": forms.Textarea(attrs={"rows": 2, "class": "span2"}),
            "knowledge": forms.Textarea(attrs={"rows": 3, "class": "span2"}),
            "alignment": forms.Select(),
            "importance": forms.Select(choices=IMPORTANCE_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("matter", None)
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()

    def clean_phone(self):
        value = self.cleaned_data.get("phone")
        if value:
            normalized, is_valid = normalize_phone(value)
            if not is_valid:
                raise ValidationError("Enter a valid 10-digit US phone number.")
            return normalized
        return value
