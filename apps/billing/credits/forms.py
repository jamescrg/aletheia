from datetime import datetime

from django import forms

from apps.billing.credits.models import Credit


class CreditsForm(forms.ModelForm):
    class Meta:
        model = Credit
        fields = ["matter", "date", "detail", "amount"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "detail": forms.TextInput(attrs={"required": False}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["date"].initial = datetime.now().date()
