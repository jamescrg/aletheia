"""List the LawPay/AffiniPay merchant's deposit accounts.

Pulls GET /v1/merchant with the configured LAWPAY_SECRET_KEY and prints each
account's id / name and whether it's the operating or trust account, plus any
eCheck (ACH) accounts. Use the printed ids to pin LAWPAY_OPERATING_ACCOUNT_ID
(and a trust id) so a charge can target the right account.

A TEST secret key sees test accounts only; a LIVE key sees live accounts. If the
list is empty, no deposit accounts are provisioned for that environment yet.
"""

from django.core.management.base import BaseCommand

from apps.invoicing.processors.lawpay import LawPayProcessor


class Command(BaseCommand):
    help = "List LawPay/AffiniPay merchant deposit accounts (operating vs trust)."

    def handle(self, *args, **options):
        merchant = LawPayProcessor().list_merchant_accounts()
        self.stdout.write(f"Merchant: {merchant.get('name')} ({merchant.get('id')})")

        accounts = merchant.get("merchant_accounts") or []
        if not accounts:
            self.stdout.write(
                self.style.WARNING(
                    "No merchant_accounts provisioned for this key's environment. "
                    "A test key only sees test accounts — provision them in the "
                    "AffiniPay sandbox, or run with the live secret key to see "
                    "live accounts."
                )
            )
        for a in accounts:
            kind = "TRUST" if a.get("trust_account") else "operating"
            self.stdout.write(f"  [{kind:9}] {a.get('name')!r:24} id={a.get('id')}")

        for a in merchant.get("ach_accounts") or []:
            self.stdout.write(
                f"  [eCheck   ] {a.get('name')!r:24} id={a.get('id')} "
                f"status={a.get('status')}"
            )
