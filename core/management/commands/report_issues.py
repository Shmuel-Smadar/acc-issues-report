import os
import time
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from core.services.acc_client import ACCClient
from core.services.aggregate import IssueAggregator
from core.services.csv_export import rows_to_csv
from core.services.auth import AuthExpired
import requests


class Command(BaseCommand):
    help = "Generate ACC Issues CSV for PDFs in target project"

    def handle(self, *args, **options):
        try:
            client = ACCClient()
            rows = IssueAggregator(client).collect_rows()

            os.makedirs(settings.REPORT_OUTPUT_DIR, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = os.path.join(settings.REPORT_OUTPUT_DIR, f"acc_issues_{ts}.csv")
            with open(path, "wb") as f:
                f.write(rows_to_csv(rows))
            self.stdout.write(self.style.SUCCESS(f"Wrote {path} ({len(rows)} rows)"))

        except AuthExpired:
            raise CommandError(
                "Not authenticated with Autodesk yet.\n"
                "Start your Django server and complete login at /auth/login/ in a browser, "
                "then re-run: manage.py report_issues"
            )

        except RuntimeError as e:
            msg = str(e)
            if "Not authenticated" in msg:
                raise CommandError(
                    "Not authenticated with Autodesk yet.\n"
                    "Start your Django server and complete login in a browser, "
                    "then re-run: manage.py report_issues"
                )
            raise CommandError(msg)

        except requests.RequestException as e:
            raise CommandError(f"Network error calling Autodesk APIs: {e}")