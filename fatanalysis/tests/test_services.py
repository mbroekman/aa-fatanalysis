"""Unit tests for aa-fatanalysis services."""

import responses
from allianceauth.eveonline.models import EveCharacter
from django.contrib.auth.models import User
from django.test import TestCase

from fatanalysis.models import FatEntry, FatSyncConfig
from fatanalysis.services import AfatScraperService, FatAggregationService, FatIngestionService

SAMPLE_CSV = """Main Character,Active for Corporation Tracking,Total FATs,Strategic & Deployment,QRF,Ghost,Bash
raz1980,1,13,8,0,2,3
Mor Dovorot,1,15,1,0,0,14
Maddog Broekman,1,59,12,3,2,42
Inactive Pilot,,0,0,0,0,0
"""

SAMPLE_HTML_TABLE = """
<table>
    <thead>
        <tr>
            <th>Main Character</th>
            <th>Active for Corporation Tracking</th>
            <th>Total FATs</th>
            <th>Strategic</th>
            <th>QRF</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Pilot Alpha</td>
            <td>1</td>
            <td>25</td>
            <td>15</td>
            <td>10</td>
        </tr>
        <tr>
            <td>Pilot Beta</td>
            <td>0</td>
            <td>5</td>
            <td>2</td>
            <td>3</td>
        </tr>
    </tbody>
</table>
"""

SAMPLE_CORP_MAIN_HTML = """
<table id="corp-main-characters">
    <thead>
        <tr><th>Character</th><th>FATs</th><th></th></tr>
    </thead>
    <tbody>
        <tr>
            <td>Pilot Alpha</td>
            <td>15</td>
            <td><button class="btn" data-character-id="918578105"></button></td>
        </tr>
        <tr>
            <td>Pilot Beta</td>
            <td>5</td>
            <td><button class="btn" data-character-id="920000001"></button></td>
        </tr>
    </tbody>
</table>
"""


class TestServices(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="director", password="password")
        cls.character = EveCharacter.objects.create(
            character_id=918578105,
            character_name="Maddog Broekman",
            corporation_id=98089258,
            corporation_name="Game of Drones",
            corporation_ticker="3GODS",
        )
        cls.config = FatSyncConfig.get_solo()
        cls.config.session_cookie = "mock_session_id_12345"
        cls.config.save()

    def test_parse_csv(self):
        records = FatIngestionService.parse_csv(SAMPLE_CSV)
        self.assertEqual(len(records), 4)

        rec1 = records[0]
        self.assertEqual(rec1["character_name"], "raz1980")
        self.assertTrue(rec1["is_main"])
        self.assertEqual(rec1["total_fats"], 13)
        self.assertEqual(rec1["fat_details"]["Strategic & Deployment"], 8)
        self.assertEqual(rec1["fat_details"]["Bash"], 3)

        rec4 = records[3]
        self.assertEqual(rec4["character_name"], "Inactive Pilot")
        self.assertFalse(rec4["is_main"])
        self.assertEqual(rec4["total_fats"], 0)

    def test_parse_csv_empty(self):
        self.assertEqual(FatIngestionService.parse_csv(""), [])
        self.assertEqual(FatIngestionService.parse_csv("   "), [])

    def test_parse_html_table(self):
        records = FatIngestionService.parse_html_table(SAMPLE_HTML_TABLE)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["character_name"], "Pilot Alpha")
        self.assertEqual(records[0]["total_fats"], 25)
        self.assertEqual(records[0]["fat_details"]["Strategic"], 15)

    def test_parse_html_corp_main_characters(self):
        records = FatIngestionService.parse_html_table(SAMPLE_CORP_MAIN_HTML)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]["character_name"], "Pilot Alpha")
        self.assertEqual(records[0]["total_fats"], 15)
        self.assertEqual(records[0]["character_id"], 918578105)
        self.assertTrue(records[0]["is_main"])
        self.assertEqual(records[1]["character_name"], "Pilot Beta")
        self.assertEqual(records[1]["total_fats"], 5)
        self.assertEqual(records[1]["character_id"], 920000001)

    def test_ingest_records_atomic(self):
        records = FatIngestionService.parse_csv(SAMPLE_CSV)
        period = FatIngestionService.ingest_records(
            corporation_id=98089258,
            corporation_name="Game of Drones",
            year=2026,
            month=8,
            records=records,
            synced_by=self.user,
        )

        self.assertEqual(period.year, 2026)
        self.assertEqual(period.month, 8)
        self.assertEqual(period.total_fats, 13 + 15 + 59)
        self.assertEqual(period.entries.count(), 4)

        # Verify linked EveCharacter
        maddog_entry = FatEntry.objects.get(period=period, character_name="Maddog Broekman")
        self.assertIsNotNone(maddog_entry.character)
        self.assertEqual(maddog_entry.character.character_id, 918578105)

        # Ingesting again for same period replaces cleanly (idempotence)
        period2 = FatIngestionService.ingest_records(
            corporation_id=98089258,
            corporation_name="Game of Drones",
            year=2026,
            month=8,
            records=records[:2],
            synced_by=self.user,
        )
        self.assertEqual(period2.pk, period.pk)
        self.assertEqual(period2.entries.count(), 2)

    @responses.activate
    def test_scraper_connection_success(self):
        scraper = AfatScraperService(config=self.config)
        responses.add(
            responses.GET,
            self.config.source_url,
            body="<html><body><h1>Dashboard</h1></body></html>",
            status=200,
        )

        success, msg = scraper.test_connection()
        self.assertTrue(success)
        self.assertIn("Successfully connected", str(msg))

    @responses.activate
    def test_scraper_connection_login_redirect(self):
        scraper = AfatScraperService(config=self.config)
        responses.add(
            responses.GET,
            self.config.source_url,
            body='<html><body><form name="login">Login</form></body></html>',
            status=200,
        )

        success, msg = scraper.test_connection()
        self.assertFalse(success)
        self.assertIn("expired or invalid", str(msg))

    def test_scraper_connection_no_cookie(self):
        self.config.session_cookie = ""
        self.config.save()
        scraper = AfatScraperService(config=self.config)
        success, msg = scraper.test_connection()
        self.assertFalse(success)
        self.assertIn("No session cookie", str(msg))

    @responses.activate
    def test_scraper_fetch_report(self):
        self.config.session_cookie = "valid_cookie"
        self.config.save()
        scraper = AfatScraperService(config=self.config)

        target_url = "https://zero.the-initiative.rocks/fleet-activity-tracking/reports/show/98089258/15/"
        responses.add(
            responses.GET,
            target_url,
            body=SAMPLE_CSV,
            status=200,
        )

        content = scraper.fetch_report(target_url)
        self.assertEqual(content, SAMPLE_CSV)

    def test_build_report_url(self):
        scraper = AfatScraperService(config=self.config)
        url = scraper.build_report_url(2026, 10)
        expected = "https://zero.the-initiative.rocks/fleet-activity-tracking/statistics/corporation/98089258/2026/10/"
        self.assertEqual(url, expected)

    @responses.activate
    def test_crawl_all_periods(self):
        self.config.session_cookie = "valid_cookie"
        self.config.save()
        scraper = AfatScraperService(config=self.config)

        # Mock two months: 2026-01 and 2026-02
        url_jan = scraper.build_report_url(2026, 1)
        url_feb = scraper.build_report_url(2026, 2)
        responses.add(responses.GET, url_jan, body=SAMPLE_CORP_MAIN_HTML, status=200)
        responses.add(responses.GET, url_feb, body="<html><body>No table</body></html>", status=200)

        summary = scraper.crawl_all_periods(start_year=2026, end_year=2026, end_month=2)
        self.assertEqual(summary["ingested_periods"], 1)
        self.assertEqual(summary["skipped_periods"], 1)
        self.assertEqual(summary["total_fats"], 20)

    def test_aggregation_service_windows(self):
        # Create 4 consecutive monthly periods: 2026-05, 2026-06, 2026-07, 2026-08
        for month in (5, 6, 7, 8):
            records = [
                {
                    "character_name": "Pilot A",
                    "is_main": True,
                    "total_fats": month * 2,
                    "fat_details": {"Strategic": month},
                },
                {"character_name": "Pilot B", "is_main": False, "total_fats": month, "fat_details": {"QRF": month}},
            ]
            FatIngestionService.ingest_records(
                corporation_id=98089258,
                corporation_name="Game of Drones",
                year=2026,
                month=month,
                records=records,
            )

        # Test 30d window: should return latest period (August 2026)
        agg_30d = FatAggregationService.aggregate_data(corporation_id=98089258, window="30d")
        self.assertEqual(len(agg_30d["periods"]), 1)
        self.assertEqual(agg_30d["periods"][0].month, 8)
        self.assertEqual(agg_30d["total_fats"], 8 * 2 + 8)

        # Test 90d window: should return last 3 periods (June, July, August)
        agg_90d = FatAggregationService.aggregate_data(corporation_id=98089258, window="90d")
        self.assertEqual(len(agg_90d["periods"]), 3)
        self.assertEqual([p.month for p in agg_90d["periods"]], [6, 7, 8])

        # Test 120d window: should return all 4 periods
        agg_120d = FatAggregationService.aggregate_data(corporation_id=98089258, window="120d")
        self.assertEqual(len(agg_120d["periods"]), 4)

        # Test all window: should return all periods
        agg_all = FatAggregationService.aggregate_data(corporation_id=98089258, window="all")
        self.assertEqual(len(agg_all["periods"]), 4)
        self.assertEqual(len(agg_all["pilots"]), 2)
        self.assertEqual(agg_all["pilots"][0]["character_name"], "Pilot A")
        self.assertEqual(agg_all["pilots"][0]["total_fats"], (5 + 6 + 7 + 8) * 2)

        # Check dynamic headers
        self.assertIn("Strategic", agg_all["dynamic_headers"])
        self.assertIn("QRF", agg_all["dynamic_headers"])
