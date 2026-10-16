"""Unit tests for aa-fatanalysis models."""

from datetime import date

from allianceauth.eveonline.models import EveCharacter, EveCorporationInfo
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase

from fatanalysis.models import FatEntry, FatMonthPeriod, FatSyncConfig, General


class TestFatModels(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username="testuser", password="password")
        cls.corp = EveCorporationInfo.objects.create(
            corporation_id=98089258,
            corporation_name="Game of Drones",
            corporation_ticker="3GODS",
            member_count=100,
        )
        cls.character = EveCharacter.objects.create(
            character_id=918578105,
            character_name="Maddog Broekman",
            corporation_id=98089258,
            corporation_name="Game of Drones",
            corporation_ticker="3GODS",
        )

    def test_general_permissions(self):
        perms = dict(General._meta.permissions)
        self.assertIn("basic_access", perms)
        self.assertIn("manage_fatanalysis", perms)

    def test_sync_config_get_solo(self):
        config = FatSyncConfig.get_solo()
        self.assertEqual(config.corporation_id, 98089258)
        self.assertEqual(config.corporation_name, "Game of Drones")
        self.assertIn("the-initiative.rocks", config.source_url)

        # Calling get_solo again returns the same record
        config2 = FatSyncConfig.get_solo()
        self.assertEqual(config.pk, config2.pk)
        self.assertEqual(str(config), "Game of Drones (98089258) Config")

    def test_fat_month_period(self):
        period = FatMonthPeriod.objects.create(
            corporation_id=98089258,
            corporation_name="Game of Drones",
            year=2026,
            month=8,
            synced_by=self.user,
        )
        self.assertEqual(period.period_date, date(2026, 8, 1))
        self.assertEqual(period.label, "August 2026")
        self.assertIn("2026-08", str(period))

        # Test unique constraint on [corporation_id, year, month]
        with self.assertRaises(IntegrityError):
            FatMonthPeriod.objects.create(
                corporation_id=98089258,
                corporation_name="Duplicate",
                year=2026,
                month=8,
            )

    def test_fat_entry_and_counts(self):
        period = FatMonthPeriod.objects.create(
            corporation_id=98089258,
            corporation_name="Game of Drones",
            year=2026,
            month=7,
        )

        entry1 = FatEntry.objects.create(
            period=period,
            character=self.character,
            character_name="Maddog Broekman",
            is_main=True,
            total_fats=15,
            fat_details={"Strategic": 10, "QRF": 5},
        )
        FatEntry.objects.create(
            period=period,
            character_name="Inactive Alt",
            is_main=False,
            total_fats=0,
            fat_details={},
        )

        self.assertEqual(period.total_pilots_count, 2)
        self.assertEqual(period.active_pilots_count, 1)
        self.assertIn("Maddog Broekman", str(entry1))

        # Test unique constraint on [period, character_name]
        with self.assertRaises(IntegrityError):
            FatEntry.objects.create(
                period=period,
                character_name="Maddog Broekman",
                total_fats=5,
            )
