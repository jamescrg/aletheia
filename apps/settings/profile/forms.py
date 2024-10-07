from django import forms

from apps.accounts.models import CustomUser


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "initials",
        ]


class ChangePasswordForm(forms.ModelForm):
    old_password = forms.CharField(widget=forms.PasswordInput)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()

        old_password = cleaned_data.get("old_password")
        if not self.instance.check_password(old_password):
            raise forms.ValidationError("Old password is incorrect")

        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password != confirm_password:
            raise forms.ValidationError("New passwords do not match")

        return cleaned_data

    def save(self, commit=True):
        password = self.cleaned_data["new_password"]
        self.instance.set_password(password)

        if commit:
            self.instance.save()

        return self.instance

    class Meta:
        model = CustomUser
        fields = ["old_password", "new_password", "confirm_password"]
