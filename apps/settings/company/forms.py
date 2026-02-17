from django import forms

from apps.settings.models import Company


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            "name",
            "address_line_1",
            "address_line_2",
            "city",
            "state",
            "zip_code",
            "phone",
            "email",
            "logo",
        ]
        widgets = {
            "logo": forms.ClearableFileInput(),
        }
