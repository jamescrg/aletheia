from django import forms
from django.urls import reverse

from apps.invoicing.requests.models import PaymentRequest
from config.settings import CustomFormRendererCompact


class PaymentRequestForm(forms.ModelForm):
    class Meta:
        model = PaymentRequest
        fields = ["matter", "recipient_email"]
        widgets = {
            "matter": forms.Select(),
            "recipient_email": forms.EmailInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.renderer = CustomFormRendererCompact()
        # On matter change, auto-fill the recipient with that matter's client
        # email by swapping in a fresh recipient input (see requests_matter_email).
        self.fields["matter"].widget.attrs.update(
            {
                "hx-get": reverse("invoicing:requests-matter-email"),
                "hx-trigger": "change",
                "hx-target": "#id_recipient_email",
                "hx-swap": "outerHTML",
            }
        )
