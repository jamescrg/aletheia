from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import CreateView

from .forms import CustomUserCreationForm, VerificationCodeForm
from .models import CustomUser, EmailVerificationCode


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = "/accounts/login/"
    template_name = "registration/signup.html"


class LoginView(View):
    """Step 1: Validate username/password, then send verification code."""

    template_name = "registration/login.html"

    def get(self, request):
        # If user is already authenticated, redirect
        if request.user.is_authenticated:
            return redirect(settings.LOGIN_REDIRECT_URL)
        form = AuthenticationForm()
        return render(
            request,
            self.template_name,
            {"form": form, "next": request.GET.get("next", "")},
        )

    def post(self, request):
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.POST.get("next") or request.GET.get("next", "")
            return redirect(next_url or settings.LOGIN_REDIRECT_URL)

        # Invalid credentials - show form with errors
        return render(
            request,
            self.template_name,
            {"form": form, "next": request.POST.get("next", "")},
        )


class VerifyCodeView(View):
    """Step 2: Verify the emailed code and complete login."""

    template_name = "registration/verify_code.html"

    def get(self, request):
        # Ensure user went through step 1
        if "pending_user_id" not in request.session:
            return redirect("accounts:login")

        form = VerificationCodeForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        # Ensure user went through step 1
        pending_user_id = request.session.get("pending_user_id")
        if not pending_user_id:
            return redirect("accounts:login")

        form = VerificationCodeForm(request.POST)

        if form.is_valid():
            code = form.cleaned_data["code"]

            try:
                user = CustomUser.objects.get(id=pending_user_id)
                verification = EmailVerificationCode.objects.get(user=user, code=code)

                if verification.is_expired():
                    # Code expired
                    verification.delete()
                    return render(
                        request,
                        self.template_name,
                        {
                            "form": form,
                            "error": "Code has expired. Please log in again.",
                        },
                    )

                # Success - clean up and log in
                verification.delete()
                del request.session["pending_user_id"]
                next_url = request.session.pop("login_next_url", None)
                login(request, user)
                return redirect(next_url or settings.LOGIN_REDIRECT_URL)

            except (CustomUser.DoesNotExist, EmailVerificationCode.DoesNotExist):
                return render(
                    request,
                    self.template_name,
                    {"form": form, "error": "Invalid verification code."},
                )

        return render(request, self.template_name, {"form": form})
