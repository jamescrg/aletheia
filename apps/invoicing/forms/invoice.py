from datetime import datetime

from django import forms

from apps.invoicing.models import Invoice


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            "matter",
            "date_from",
            "date_to",
            "issue_date",
            "message",
            "comment",
            "show_comp",
            "discount",
        ]
        widgets = {
            "matter": forms.Select(attrs={"required": True}),
            "date_from": forms.DateInput(attrs={"type": "date"}),
            "date_to": forms.DateInput(attrs={"type": "date"}),
            "issue_date": forms.DateInput(attrs={"type": "date"}),
            "message": forms.Textarea(attrs={"rows": 3}),
            "comment": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["issue_date"].initial = datetime.now()
