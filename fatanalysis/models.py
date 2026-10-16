import calendar
from datetime import date

from allianceauth.eveonline.models import EveCharacter
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class General(models.Model):
    """
    Meta model for app permissions.
    """

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (
            ("basic_access", "Can access this app"),
            ("manage_fatanalysis", "Can manage and sync FAT data"),
        )


class FatSyncConfig(models.Model):
    """
    Configuration for fetching/syncing FAT data from external sources (e.g. INIT Auth AFAT).
    Singleton or per-corporation configuration managed entirely via frontend UI.
    """

    corporation_id = models.BigIntegerField(default=98089258, unique=True, verbose_name=_("Corporation ID"))
    corporation_name = models.CharField(max_length=255, default="Game of Drones", verbose_name=_("Corporation Name"))
    source_url = models.URLField(
        default="https://zero.the-initiative.rocks/fleet-activity-tracking/",
        verbose_name=_("Source URL"),
    )
    session_cookie = models.TextField(
        blank=True,
        default="",
        verbose_name=_("Session Cookie (sessionid)"),
        help_text=_("The active sessionid cookie from the source Alliance Auth instance."),
    )
    user_agent = models.CharField(
        max_length=255,
        default=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        blank=True,
    )
    last_sync_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Last Sync At"))
    last_sync_status = models.CharField(max_length=64, default="never", verbose_name=_("Last Sync Status"))
    last_sync_log = models.TextField(blank=True, default="", verbose_name=_("Last Sync Log"))

    class Meta:
        verbose_name = _("FAT Sync Configuration")
        verbose_name_plural = _("FAT Sync Configurations")

    def __str__(self) -> str:
        return f"{self.corporation_name} ({self.corporation_id}) Config"

    @classmethod
    def get_solo(cls) -> "FatSyncConfig":
        config, _ = cls.objects.get_or_create(
            corporation_id=98089258,
            defaults={"corporation_name": "Game of Drones"},
        )
        return config


class FatMonthPeriod(models.Model):
    """
    Represents a specific monthly recording period for a corporation.
    """

    corporation_id = models.BigIntegerField(db_index=True, verbose_name=_("Corporation ID"))
    corporation_name = models.CharField(max_length=255, verbose_name=_("Corporation Name"))
    year = models.IntegerField(db_index=True, verbose_name=_("Year"))
    month = models.IntegerField(db_index=True, verbose_name=_("Month"))
    total_fats = models.IntegerField(default=0, verbose_name=_("Total FATs"))
    fats_by_time = models.JSONField(default=dict, blank=True, verbose_name=_("FATs by Time"))
    fats_by_weekday = models.JSONField(default=dict, blank=True, verbose_name=_("FATs by Weekday"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    synced_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="synced_fat_periods",
    )

    class Meta:
        verbose_name = _("FAT Monthly Period")
        verbose_name_plural = _("FAT Monthly Periods")
        ordering = ["-year", "-month"]
        constraints = [
            models.UniqueConstraint(fields=["corporation_id", "year", "month"], name="unique_corp_year_month")
        ]

    def __str__(self) -> str:
        return f"{self.corporation_name} - {self.year}-{self.month:02d} ({self.total_fats} FATs)"

    @property
    def period_date(self) -> date:
        return date(self.year, self.month, 1)

    @property
    def label(self) -> str:
        month_name = calendar.month_name[self.month]
        return f"{month_name} {self.year}"

    @property
    def total_pilots_count(self) -> int:
        return self.entries.count()

    @property
    def active_pilots_count(self) -> int:
        return self.entries.filter(total_fats__gt=0).count()


class FatEntry(models.Model):
    """
    Individual character participation in a monthly period.
    """

    period = models.ForeignKey(FatMonthPeriod, on_delete=models.CASCADE, related_name="entries")
    character = models.ForeignKey(
        EveCharacter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fat_entries",
    )
    character_name = models.CharField(max_length=255, db_index=True, verbose_name=_("Character Name"))
    main_character_id = models.BigIntegerField(
        null=True, blank=True, db_index=True, verbose_name=_("Main Character ID")
    )
    main_character_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name=_("Main Character Name"),
    )
    is_main = models.BooleanField(default=False, verbose_name=_("Is Main Character"))
    total_fats = models.IntegerField(default=0, verbose_name=_("Total FATs"))
    ship_details = models.JSONField(default=dict, blank=True, verbose_name=_("Ship Details"))
    fat_details = models.JSONField(default=dict, blank=True, verbose_name=_("FAT Details"))

    class Meta:
        verbose_name = _("FAT Entry")
        verbose_name_plural = _("FAT Entries")
        ordering = ["-total_fats", "character_name"]
        constraints = [
            models.UniqueConstraint(fields=["period", "character_name"], name="unique_period_character_name")
        ]

    def __str__(self) -> str:
        return f"{self.character_name} - {self.total_fats} FATs ({self.period.year}-{self.period.month:02d})"
