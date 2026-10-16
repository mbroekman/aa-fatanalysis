"""Unit tests for aa-fatanalysis views."""

from django.contrib.auth.models import Permission, User
from django.test import Client, TestCase
from django.urls import reverse

from fatanalysis.models import FatMonthPeriod, FatSyncConfig
from fatanalysis.services import FatIngestionService

SAMPLE_CSV = """Main Character,Active for Corporation Tracking,Total FATs,Strategic,QRF
TestPilot,1,10,6,4
"""


class TestViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Users
        cls.member_user = User.objects.create_user(username="member", password="password")
        cls.director_user = User.objects.create_user(username="director", password="password")
        cls.unprivileged_user = User.objects.create_user(username="stranger", password="password")

        # Permissions
        basic_perm = Permission.objects.get(codename="basic_access", content_type__app_label="fatanalysis")
        manage_perm = Permission.objects.get(codename="manage_fatanalysis", content_type__app_label="fatanalysis")

        cls.member_user.user_permissions.add(basic_perm)
        cls.director_user.user_permissions.add(basic_perm, manage_perm)

        # Config & Sample Period
        cls.config = FatSyncConfig.get_solo()
        records = FatIngestionService.parse_csv(SAMPLE_CSV)
        cls.period = FatIngestionService.ingest_records(
            corporation_id=98089258,
            corporation_name="Game of Drones",
            year=2026,
            month=8,
            records=records,
            synced_by=cls.director_user,
        )

    def setUp(self):
        self.client = Client()

    def test_anonymous_redirect(self):
        resp = self.client.get(reverse("fatanalysis:index"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/account/login", resp.url)

    def test_unprivileged_user_forbidden(self):
        self.client.login(username="stranger", password="password")
        resp = self.client.get(reverse("fatanalysis:index"))
        self.assertEqual(resp.status_code, 403)

    def test_member_index_views(self):
        self.client.login(username="member", password="password")

        # Index with default window
        resp = self.client.get(reverse("fatanalysis:index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Fleet Activity Tracking")
        self.assertContains(resp, "TestPilot")

        # Index with specific window
        resp_30d = self.client.get(reverse("fatanalysis:index") + "?window=30d")
        self.assertEqual(resp_30d.status_code, 200)

        # Legacy redirects
        resp_leg = self.client.get(reverse("fatanalysis:overview_legacy", args=[30]))
        self.assertEqual(resp_leg.status_code, 302)

    def test_member_index_empty_state(self):
        self.client.login(username="member", password="password")
        FatMonthPeriod.objects.all().delete()
        resp = self.client.get(reverse("fatanalysis:index"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'colspan="5"')
        self.assertContains(resp, "No pilot FAT entries recorded for this time window.")

    def test_member_player_detail(self):
        self.client.login(username="member", password="password")
        resp = self.client.get(reverse("fatanalysis:player_detail", args=["TestPilot"]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "TestPilot")
        self.assertContains(resp, "August 2026")

        # Unknown player redirects
        resp_unknown = self.client.get(reverse("fatanalysis:player_detail", args=["NonExistentPilot"]))
        self.assertEqual(resp_unknown.status_code, 302)

    def test_period_list_and_detail(self):
        self.client.login(username="member", password="password")

        # Period list
        resp_list = self.client.get(reverse("fatanalysis:period_list"))
        self.assertEqual(resp_list.status_code, 200)
        self.assertContains(resp_list, "August 2026")

        # Period detail
        resp_detail = self.client.get(reverse("fatanalysis:period_detail", args=[self.period.id]))
        self.assertEqual(resp_detail.status_code, 200)
        self.assertContains(resp_detail, "TestPilot")

    def test_sync_management_permission_denied_for_member(self):
        self.client.login(username="member", password="password")
        resp = self.client.get(reverse("fatanalysis:sync_management"))
        self.assertEqual(resp.status_code, 403)

    def test_sync_management_director_get(self):
        self.client.login(username="director", password="password")
        resp = self.client.get(reverse("fatanalysis:sync_management"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "AFAT Sync & Ingestion Management")
        self.assertContains(resp, "INIT Auth Scraper")

    def test_sync_management_save_config(self):
        self.client.login(username="director", password="password")
        post_data = {
            "action": "save_config",
            "corporation_id": 98089258,
            "corporation_name": "Game of Drones",
            "source_url": "https://zero.the-initiative.rocks/fleet-activity-tracking/",
            "session_cookie": "new_session_id_xyz",
            "user_agent": "CustomAgent/1.0",
        }
        resp = self.client.post(reverse("fatanalysis:sync_management"), post_data)
        self.assertEqual(resp.status_code, 302)

        config = FatSyncConfig.get_solo()
        self.assertEqual(config.session_cookie, "new_session_id_xyz")

    def test_sync_management_direct_csv_import(self):
        self.client.login(username="director", password="password")
        post_data = {
            "action": "direct_csv_import",
            "year": 2026,
            "month": 9,
            "corporation_name": "Game of Drones",
            "csv_text": SAMPLE_CSV,
        }
        resp = self.client.post(reverse("fatanalysis:sync_management"), post_data)
        self.assertEqual(resp.status_code, 302)

        # Verify created period
        new_period = FatMonthPeriod.objects.get(year=2026, month=9)
        self.assertEqual(new_period.total_fats, 10)
        self.assertEqual(new_period.entries.count(), 1)

    def test_period_delete(self):
        self.client.login(username="director", password="password")
        period_to_delete = FatMonthPeriod.objects.create(
            corporation_id=98089258,
            corporation_name="Game of Drones",
            year=2025,
            month=1,
            total_fats=5,
        )

        resp_get = self.client.get(reverse("fatanalysis:period_delete", args=[period_to_delete.id]))
        self.assertEqual(resp_get.status_code, 200)

        resp_post = self.client.post(reverse("fatanalysis:period_delete", args=[period_to_delete.id]))
        self.assertEqual(resp_post.status_code, 302)
        self.assertFalse(FatMonthPeriod.objects.filter(id=period_to_delete.id).exists())
