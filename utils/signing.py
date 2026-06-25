"""Signed, expiring tokens for public (no-login) URLs.

The app is otherwise entirely `@login_required`; the invoice payment page is the
first public surface that exposes a specific record. Instead of a guessable
URL, we hand out an opaque token that (a) names the invoice by its `uuid` (never
the sequential pk) and (b) is signed with the project SECRET_KEY and stamped
with a timestamp, so it cannot be forged and expires on its own.

Built on `django.core.signing` (TimestampSigner + JSON). Rotating an invoice's
`uuid` invalidates every outstanding link for it.
"""

from django.core import signing

# Namespacing salt — keeps these tokens from being interchangeable with any
# other use of signing.dumps elsewhere in the project.
_PAY_SALT = "invoicing.invoice-payment"


def make_payment_token(invoice) -> str:
    """Opaque signed token granting payment access to `invoice`."""
    return signing.dumps(str(invoice.uuid), salt=_PAY_SALT)


def read_payment_token(token: str, *, max_age=None) -> str:
    """Return the invoice uuid encoded in `token`.

    Raises `signing.SignatureExpired` if older than `max_age` seconds, or
    `signing.BadSignature` if tampered/invalid. Callers translate these into a
    friendly "link expired / invalid" page.
    """
    return signing.loads(token, salt=_PAY_SALT, max_age=max_age)
