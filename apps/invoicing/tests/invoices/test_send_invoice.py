import pytest

from apps.invoicing.invoices.functions.send_invoice import (
    _invalid_addresses,
    _parse_recipients,
)


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("", []),
        (None, []),
        ("a@x.com", ["a@x.com"]),
        ("a@x.com, b@y.com", ["a@x.com", "b@y.com"]),
        ("a@x.com,b@y.com", ["a@x.com", "b@y.com"]),
        ("  a@x.com ;  b@y.com ", ["a@x.com", "b@y.com"]),  # ; is treated as ,
        ("a@x.com, , b@y.com,", ["a@x.com", "b@y.com"]),  # blanks dropped
    ],
)
def test_parse_recipients(raw, expected):
    assert _parse_recipients(raw) == expected


def test_invalid_addresses_flags_only_bad_ones():
    addrs = ["good@x.com", "not-an-email", "also@good.org", "@nope"]
    assert _invalid_addresses(addrs) == ["not-an-email", "@nope"]


def test_invalid_addresses_empty_when_all_valid():
    assert _invalid_addresses(["a@x.com", "b@y.com"]) == []
