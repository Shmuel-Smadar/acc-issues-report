import os
import time
import logging
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
        logger = logging.getLogger("app")
        logger.info("event=report.cli_start project=%s", settings.TARGET_PROJECT_NAME)
        try:
            client = ACCClient()
            rows = IssueAggregator(client).collect_rows()
            os.makedirs(settings.REPORT_OUTPUT_DIR, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = os.path.join(settings.REPORT_OUTPUT_DIR, f"acc_issues_{ts}.csv")
            content = rows_to_csv(rows)
            with open(path, "wb") as f:
                f.write(content)
            logger.info("event=report.cli_written path=%s rows=%s bytes=%s", path, len(rows), len(content))
            self.stdout.write(self.style.SUCCESS(f"Wrote {path} ({len(rows)} rows)"))
        except AuthExpired:
            logger.error("event=report.cli_error type=auth_expired")
            raise CommandError(
                "Not authenticated with Autodesk yet.\n"
                "Start your Django server and complete login at /auth/login/ in a browser, "
                "then re-run: manage.py report_issues"
            )
        except RuntimeError as e:
            msg = str(e)
            if "Not authenticated" in msg:
                logger.error("event=report.cli_error type=not_authenticated")
                raise CommandError(
                    "Not authenticated with Autodesk yet.\n"
                    "Start your Django server and complete login in a browser, "
                    "then re-run: manage.py report_issues"
                )
            logger.error("event=report.cli_error type=runtime error=%s", msg)
            raise CommandError(msg)
        except requests.RequestException as e:
            logger.error("event=report.cli_error type=network error=%s", type(e).__name__)
            raise CommandError(f"Network error calling Autodesk APIs: {e}")
