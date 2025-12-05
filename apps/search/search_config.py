"""Watson search registration for global search models."""

from watson import search as watson

from apps.contacts.models import Contact
from apps.intakes.models import Intake
from apps.matters.models import Matter
from apps.matters.proceedings.models import Proceeding

# Register Matter model for search
watson.register(
    Matter,
    fields=("name", "work_status", "description"),
)

# Register Contact model for search
watson.register(
    Contact,
    fields=("name", "company", "email", "phone1", "phone2", "phone3", "notes"),
)

# Register Proceeding model for search
watson.register(
    Proceeding,
    fields=("case_number", "forum"),
)

# Register Intake model for search
watson.register(
    Intake,
    fields=("name", "email", "phone"),
)
