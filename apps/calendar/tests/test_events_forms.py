import pytest

from apps.calendar.forms import EventForm

pytestmark = pytest.mark.django_db


def test_form_valid(matter, event_data):
    data = event_data
    data["matter"] = matter.id
    form = EventForm(data)
    assert form.is_valid()


# -----------------------------------------------------
# clean_description tests
# -----------------------------------------------------
def test_description_too_short(matter, event_data):
    data = event_data.copy()
    data["matter"] = matter.id
    data["description"] = "abc"  # 3 chars, min is 4
    form = EventForm(data)
    assert not form.is_valid()
    assert "description" in form.errors
    assert "4 or more" in form.errors["description"][0]


def test_description_too_long(matter, event_data):
    data = event_data.copy()
    data["matter"] = matter.id
    data["description"] = "a" * 201  # 201 chars, max is 200
    form = EventForm(data)
    assert not form.is_valid()
    assert "description" in form.errors
    assert "200 character" in form.errors["description"][0]


# -----------------------------------------------------
# clean() cross-field validation tests
# -----------------------------------------------------
def test_end_time_must_be_after_start_time(matter, event_data):
    data = event_data.copy()
    data["matter"] = matter.id
    data["start_time"] = "14:00"
    data["end_time"] = "13:00"  # End before start
    form = EventForm(data)
    assert not form.is_valid()
    assert "end_time" in form.errors
    assert "after start time" in form.errors["end_time"][0]


def test_end_time_same_as_start_time(matter, event_data):
    data = event_data.copy()
    data["matter"] = matter.id
    data["start_time"] = "14:00"
    data["end_time"] = "14:00"  # Same time is also invalid
    form = EventForm(data)
    assert not form.is_valid()
    assert "end_time" in form.errors


def test_valid_start_and_end_time(matter, event_data):
    data = event_data.copy()
    data["matter"] = matter.id
    data["start_time"] = "14:00"
    data["end_time"] = "15:00"  # Valid: end after start
    form = EventForm(data)
    assert form.is_valid()


def test_times_optional(matter, event_data):
    data = event_data.copy()
    data["matter"] = matter.id
    data["start_time"] = ""
    data["end_time"] = ""
    form = EventForm(data)
    assert form.is_valid()
