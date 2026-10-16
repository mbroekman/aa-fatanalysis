"""
Management command to crawl and ingest all historical AFAT statistics from INIT Auth.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from fatanalysis.services import AfatScraperService


class Command(BaseCommand):
    help = "Crawl and ingest all historical AFAT data from INIT Auth directly into FatMonthPeriod and FatEntry."

    def add_arguments(self, parser):
        now = timezone.now()
        parser.add_argument(
            "--start-year",
            type=int,
            default=2024,
            help="Starting year to crawl from (default: 2024)",
        )
        parser.add_argument(
            "--end-year",
            type=int,
            default=now.year,
            help=f"Ending year to crawl up to (default: {now.year})",
        )
        parser.add_argument(
            "--end-month",
            type=int,
            default=now.month,
            help=f"Ending month to crawl up to (default: {now.month})",
        )
        parser.add_argument(
            "--corporation-id",
            type=int,
            default=None,
            help="Corporation ID override (default: from FatSyncConfig)",
        )

    def handle(self, *args, **options):
        start_year = options["start_year"]
        end_year = options["end_year"]
        end_month = options["end_month"]

        self.stdout.write(
            self.style.NOTICE(f"Initiating AFAT bulk sync: {start_year}-01 through {end_year}-{end_month:02d}...")
        )

        scraper = AfatScraperService()
        if options.get("corporation_id"):
            scraper.config.corporation_id = options["corporation_id"]

        success, msg = scraper.test_connection()
        if not success:
            self.stderr.write(self.style.ERROR(f"Connection test failed: {msg}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Connected to {scraper.config.source_url}. Crawling..."))

        summary = scraper.crawl_all_periods(
            start_year=start_year,
            end_year=end_year,
            end_month=end_month,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Sync completed successfully! "
                f"Ingested {summary['ingested_periods']} periods ({summary['total_fats']} total FATs). "
                f"Skipped {summary['skipped_periods']} empty periods. "
                f"Failed: {summary['failed_periods']}."
            )
        )
