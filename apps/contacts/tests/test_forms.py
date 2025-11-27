import pytest

from apps.contacts.forms import ContactForm

pytestmark = pytest.mark.django_db


def test_form_valid(contact_data):
    data = contact_data
    form = ContactForm(data)
    assert form.is_valid()


def test_name(contact_data):
    data = contact_data
    data["name"] = "a"
    form = ContactForm(data)
    assert not form.is_valid()
    assert "must be greater" in form.errors["name"][0]

    data = contact_data
    data["name"] = "s" * 55
    form = ContactForm(contact_data)
    assert not form.is_valid()
    assert "must be fewer" in form.errors["name"][0]


def test_company(contact_data):
    data = contact_data
    data["company"] = "s" * 55
    form = ContactForm(contact_data)
    assert not form.is_valid()
    assert "must be fewer" in form.errors["company"][0]


def test_address(contact_data):
    data = contact_data
    data["address"] = "s" * 255
    form = ContactForm(contact_data)
    assert not form.is_valid()
    assert "must be fewer" in form.errors["address"][0]


def test_phones_and_email(contact_data):
    # Test invalid phone numbers (not 10 digits)
    data = contact_data.copy()
    data["phone1"] = "123"  # Too short
    data["phone2"] = "456"
    data["phone3"] = "789"
    form = ContactForm(data)
    assert not form.is_valid()
    assert "10-digit" in form.errors["phone1"][0]
    assert "10-digit" in form.errors["phone2"][0]
    assert "10-digit" in form.errors["phone3"][0]

    # Test valid phone number normalizes to digits
    data = contact_data.copy()
    data["phone1"] = "(406) 363-1234"
    form = ContactForm(data)
    assert form.is_valid()
    assert form.cleaned_data["phone1"] == "4063631234"

    # Test invalid email
    data = contact_data.copy()
    data["email"] = "not-an-email"
    form = ContactForm(data)
    assert not form.is_valid()
    assert "email" in form.errors["email"][0].lower()


def test_notes(contact_data):
    data = contact_data
    data["notes"] = "s" * 255
    form = ContactForm(contact_data)
    assert not form.is_valid()
    assert "must be fewer" in form.errors["notes"][0]


# -----------------------------------------------------
# website validation tests
# -----------------------------------------------------
def test_website_adds_https_scheme(contact_data):
    data = contact_data.copy()
    data["website"] = "example.com"
    form = ContactForm(data)
    assert form.is_valid()
    assert form.cleaned_data["website"] == "https://example.com"


def test_website_preserves_http_scheme(contact_data):
    data = contact_data.copy()
    data["website"] = "http://example.com"
    form = ContactForm(data)
    assert form.is_valid()
    assert form.cleaned_data["website"] == "http://example.com"


def test_website_preserves_https_scheme(contact_data):
    data = contact_data.copy()
    data["website"] = "https://example.com"
    form = ContactForm(data)
    assert form.is_valid()
    assert form.cleaned_data["website"] == "https://example.com"


def test_website_invalid_url(contact_data):
    data = contact_data.copy()
    data["website"] = "not a valid url!!!"
    form = ContactForm(data)
    assert not form.is_valid()
    assert "website" in form.errors


def test_website_too_long(contact_data):
    data = contact_data.copy()
    data["website"] = "https://" + "a" * 250 + ".com"
    form = ContactForm(data)
    assert not form.is_valid()
    assert "255 characters" in form.errors["website"][0]


# -----------------------------------------------------
# email normalization tests
# -----------------------------------------------------
def test_email_normalizes_to_lowercase(contact_data):
    data = contact_data.copy()
    data["email"] = "John.Doe@Example.COM"
    form = ContactForm(data)
    assert form.is_valid()
    assert form.cleaned_data["email"] == "john.doe@example.com"


def test_email2_normalizes_to_lowercase(contact_data):
    data = contact_data.copy()
    data["email2"] = "Jane.Doe@Example.COM"
    form = ContactForm(data)
    assert form.is_valid()
    assert form.cleaned_data["email2"] == "jane.doe@example.com"


def test_email2_invalid(contact_data):
    data = contact_data.copy()
    data["email2"] = "not-an-email"
    form = ContactForm(data)
    assert not form.is_valid()
    assert "email2" in form.errors
