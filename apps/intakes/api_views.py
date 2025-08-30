import json
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.intakes.models import Intake, Note


@csrf_exempt
@require_http_methods(["POST"])
def receive_inquiry(request):
    """
    API endpoint to receive inquiry data from external sources.
    Returns JSON response with success/failure status.
    """
    try:
        data = json.loads(request.body)

        full_name = data.get("full_name", "")
        phone_number = data.get("phone_number", "")
        email = data.get("email", "")
        summary = data.get("summary", "")

        if not all([full_name, phone_number, email, summary]):
            return JsonResponse(
                {"success": False, "error": "Missing required fields"}, status=400
            )

        intake = Intake.objects.create(
            name=full_name,
            phone=phone_number,
            date=datetime.now().date(),
            status="Open",
            email=email,
        )

        Note.objects.create(
            date=datetime.now().date(),
            time=datetime.now().time(),
            intake=intake,
            type="Email In",
            details=summary,
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Inquiry received successfully",
                "intake_id": intake.id,
            }
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "error": "Invalid JSON data"}, status=400
        )
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)
