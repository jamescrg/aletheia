from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from apps.settings.profile.forms import ChangePasswordForm, ProfileForm


def _get_form_errors(form):
    errors = []
    for field, error_list in form.errors.items():
        if field == "__all__":
            errors.extend(error_list)
        else:
            errors.extend(f"{field.capitalize()}: {error}" for error in error_list)
    return ". ".join(errors)


@login_required
def profile_index(request):
    context = {
        "subapp": "profile",
    }
    return render(request, "settings/profile/index.html", context)


@login_required
def personal_profile(request, form_type=None):
    if request.method == "POST":
        if form_type == "profile":
            form = ProfileForm(request.POST, instance=request.user)

            if form.is_valid():
                profile = form.save(commit=False)
                profile.save()

                return HttpResponse("Profile updated successfully")
        elif form_type == "password":
            change_password_form = ChangePasswordForm(
                request.POST, instance=request.user
            )

            if change_password_form.is_valid() and form_type == "password":
                user = change_password_form.save(commit=True)
                user.save()

                return HttpResponse(
                    '<div class="success-msg">Password changed successfully</div>'
                )
            else:
                errors = _get_form_errors(change_password_form)

                return HttpResponse(f'<div class="error-msg">{errors}</div>')

    else:
        form = ProfileForm(instance=request.user)
        change_password_form = ChangePasswordForm(instance=request.user)

    context = {
        "user": request.user,
        "form": form,
        "change_password_form": change_password_form,
    }

    return render(request, "settings/profile/profile.html", context)
