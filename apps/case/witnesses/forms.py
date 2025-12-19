from django import forms
from django.core.exceptions import ValidationError

from apps.case.models import Witness
from config.helpers import normalize_phone
from config.settings import CustomFormRendererCompact

# Importance choices for select widget (1-10)
IMPORTANCE_CHOICES = tuple((i, f"Importance {i}") for i in range(1, 11))


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
                    "autofocus": "autofocus",
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
