import pytest
from django.test import Client

from apps.accounts.models import CustomUser
from apps.activity.time.models import TimeEntry
from apps.matters.models import Matter, PracticeArea


@pytest.fixture
def user():
    user = CustomUser.objects.create(
        username="Ollie", email="ollie@gmail.com", user_rate=100
    )
    user.set_password("clawboy")
    user.save()

    return user


@pytest.fixture
def client(user):
    client = Client()
    client.login(username="Ollie", password="clawboy")
    client.get("/dash/")  # Set daily dash session to avoid redirect
    return client


@pytest.fixture
def practice_area():
    practice_area = PracticeArea.objects.create(name="General", is_active=True)
    return practice_area


@pytest.fixture
def matter(practice_area):
    matter = Matter.objects.create(
        name="Sample Test Matter",
        work_status="Awaiting response from OC",
        status="Open",
        practice_area=practice_area,
    )
    matter.save()
    return matter


@pytest.fixture
def entry(user, matter):
    entry = TimeEntry.objects.create(
        user_id=user.id,
        matter=matter,
        date="2020-01-07",
        actions="Call with client",
        hours=0.2,
        rate=300,
        comp=False,
        entered=False,
    )
    entry.save()
    return entry


@pytest.fixture
def entry_data(entry):
    exclude_keys = {"_state", "id", "matter_id"}

    entry_data = {
        key: value for key, value in entry.__dict__.items() if key not in exclude_keys
    }
    entry_data["matter"] = entry.matter_id

    entry_data = {k: v if v is not None else "" for k, v in entry_data.items()}

    return entry_data
