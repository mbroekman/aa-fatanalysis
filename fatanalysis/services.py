"""
Service layer for aa-fatanalysis:
- Scraper & HTTP client for INIT Auth AFAT data
- CSV & HTML parsing and atomic database ingestion
- Dynamic time-window aggregation (30d, 90d, 120d, YTD, multi-year)
"""

import calendar
import csv
import io
import logging
import re
from collections import defaultdict
from typing import Any

import requests
from allianceauth.eveonline.models import EveCharacter
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import FatEntry, FatMonthPeriod, FatSyncConfig

logger = logging.getLogger(__name__)


class AfatScraperService:
    """
    HTTP client for querying and scraping AFAT reports from INIT Auth using a session cookie.
    """

    def __init__(self, config: FatSyncConfig | None = None) -> None:
        self.config = config or FatSyncConfig.get_solo()

    def get_session(self) -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/csv,*/*;q=0.8",
            }
        )
        if self.config.session_cookie:
            session.cookies.set("sessionid", self.config.session_cookie.strip())
        return session

    def test_connection(self) -> tuple[bool, str]:
        """
        Tests whether the configured source_url is reachable and the session cookie is valid.
        """
        if not self.config.session_cookie:
            return False, str(_("No session cookie configured."))

        session = self.get_session()
        try:
            resp = session.get(self.config.source_url, timeout=15, allow_redirects=True)
            if resp.status_code != 200:
                return False, str(
                    _("HTTP error %(code)s when accessing %(url)s")
                    % {
                        "code": resp.status_code,
                        "url": self.config.source_url,
                    }
                )

            # Check if redirected to login page
            if "/account/login" in resp.url or 'name="login"' in resp.text:
                return False, str(_("Session cookie expired or invalid (redirected to login)."))

            return True, str(_("Successfully connected to source AFAT."))
        except requests.RequestException as e:
            logger.exception("Failed to connect to AFAT: %s", e)
            return False, str(_("Connection failed: %(error)s") % {"error": str(e)})

    def fetch_report(self, target_url: str) -> str:
        """
        Fetches report content (CSV or HTML) from a specific AFAT report URL.
        """
        session = self.get_session()
        resp = session.get(target_url, timeout=30, allow_redirects=True)
        resp.raise_for_status()

        if "/account/login" in resp.url:
            raise PermissionError("Session cookie is invalid or expired (redirected to login).")

        return resp.text

    def build_report_url(self, year: int, month: int, corporation_id: int | None = None) -> str:
        """
        Constructs the URL for the monthly corporation statistics page on INIT Auth.
        """
        base_url = self.config.source_url.rstrip("/")
        corp_id = corporation_id or self.config.corporation_id
        return f"{base_url}/statistics/corporation/{corp_id}/{year}/{month}/"

    def fetch_month_report(self, year: int, month: int, corporation_id: int | None = None) -> str:
        """
        Fetches the monthly statistics HTML page for a corporation from INIT Auth.
        """
        url = self.build_report_url(year, month, corporation_id)
        return self.fetch_report(url)

    def crawl_all_periods(
        self,
        start_year: int = 2024,
        end_year: int | None = None,
        end_month: int | None = None,
        synced_by: User | None = None,
    ) -> dict[str, Any]:
        """
        Crawls and ingests all monthly FAT statistics from start_year up to end_year/end_month.
        """
        now = timezone.now()
        target_end_year = end_year or now.year
        target_end_month = end_month or now.month

        summary: dict[str, Any] = {
            "ingested_periods": 0,
            "skipped_periods": 0,
            "failed_periods": 0,
            "total_fats": 0,
            "details": [],
        }

        log_lines: list[str] = [
            f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Started bulk sync from {start_year}-01 to "
            f"{target_end_year}-{target_end_month:02d}."
        ]

        # Iterate year by year, month by month
        for y in range(start_year, target_end_year + 1):
            max_m = target_end_month if y == target_end_year else 12
            for m in range(1, max_m + 1):
                period_label = f"{calendar.month_name[m]} {y}"
                try:
                    html_content = self.fetch_month_report(y, m)
                    records = FatIngestionService.parse_html_table(html_content)
                    fats_by_time, fats_by_weekday, fats_by_ship = FatIngestionService.parse_html_charts(html_content)
                    if not records and not fats_by_time and not fats_by_weekday and not fats_by_ship:
                        summary["skipped_periods"] += 1
                        log_lines.append(f"  - {period_label}: No pilot records found (skipped).")
                        continue

                    period = FatIngestionService.ingest_records(
                        corporation_id=self.config.corporation_id,
                        corporation_name=self.config.corporation_name,
                        year=y,
                        month=m,
                        records=records,
                        synced_by=synced_by,
                        fats_by_time=fats_by_time,
                        fats_by_weekday=fats_by_weekday,
                        fats_by_ship=fats_by_ship,
                    )
                    summary["ingested_periods"] += 1
                    summary["total_fats"] += period.total_fats
                    summary["details"].append(
                        {
                            "year": y,
                            "month": m,
                            "label": period.label,
                            "fats": period.total_fats,
                            "pilots": len(records),
                        }
                    )
                    log_lines.append(f"  + {period_label}: Ingested {len(records)} pilots, {period.total_fats} FATs.")
                except Exception as e:
                    logger.warning("Error fetching %s: %s", period_label, e)
                    summary["failed_periods"] += 1
                    log_lines.append(f"  ! {period_label}: Error: {e}")

        # Update config sync status
        try:
            self.config.last_sync_at = timezone.now()
            self.config.last_sync_status = "success" if summary["ingested_periods"] > 0 else "completed_empty"
            full_log = "\n".join(log_lines) + "\n\n" + (self.config.last_sync_log or "")
            self.config.last_sync_log = full_log[:4000]
            self.config.save(update_fields=["last_sync_at", "last_sync_status", "last_sync_log"])
        except Exception:
            pass

        return summary


class FatIngestionService:
    """
    Handles parsing and atomic ingestion of FAT reports into FatMonthPeriod and FatEntry models.
    """

    @staticmethod
    def parse_csv(csv_content: str) -> list[dict[str, Any]]:
        """
        Parses an AFAT export CSV string into a standardized list of record dictionaries.
        """
        if not csv_content or not csv_content.strip():
            return []

        # Strip UTF-8 BOM if present
        cleaned_content = csv_content.lstrip("\ufeff")
        reader = csv.DictReader(io.StringIO(cleaned_content))

        records: list[dict[str, Any]] = []
        standard_keys = {
            "main character",
            "character",
            "pilot",
            "character name",
            "active for corporation tracking",
            "total fats",
            "total",
            "fats",
        }

        for row in reader:
            if not row:
                continue

            # Identify character name
            char_name = (
                row.get("Main Character") or row.get("Character") or row.get("Pilot") or row.get("character_name")
            )
            if not char_name:
                # Try finding first non-empty value
                for k, v in row.items():
                    if k and k.lower() in {"main character", "character", "pilot"} and v:
                        char_name = v.strip()
                        break

            if not char_name or not char_name.strip():
                continue

            char_name = char_name.strip()

            # Active/Main flag
            active_val = row.get("Active for Corporation Tracking", "0")
            is_main = str(active_val).strip() in {"1", "true", "True", "yes", "Yes"}

            # Total FATs
            total_raw = row.get("Total FATs") or row.get("Total") or row.get("total_fats") or 0
            try:
                total_fats = int(total_raw)
            except (ValueError, TypeError):
                total_fats = 0

            # Dynamic FAT details
            fat_details: dict[str, int] = {}
            for col_name, val in row.items():
                if not col_name:
                    continue
                col_clean = col_name.strip()
                if col_clean.lower() not in standard_keys:
                    try:
                        fat_details[col_clean] = int(val) if val else 0
                    except (ValueError, TypeError):
                        pass

            records.append(
                {
                    "character_name": char_name,
                    "is_main": is_main,
                    "total_fats": total_fats,
                    "fat_details": fat_details,
                    "ship_details": {},
                }
            )

        return records

    @staticmethod
    def parse_html_table(html_content: str) -> list[dict[str, Any]]:
        """
        Parses an HTML table (from INIT Auth statistics or generic reports) into standardized records.
        Prioritizes the 'corp-main-characters' table from INIT Auth AFAT statistics.
        """
        if not html_content or not html_content.strip():
            return []

        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Prioritize standard AFAT 'corp-main-characters' table
        main_table = soup.find("table", id="corp-main-characters")
        if main_table:
            records: list[dict[str, Any]] = []
            tbody = main_table.find("tbody") or main_table
            for tr in tbody.find_all("tr"):
                td_cells = tr.find_all("td")
                if not td_cells:
                    continue
                char_name = td_cells[0].get_text(strip=True)
                if not char_name:
                    continue

                try:
                    total_fats = int(td_cells[1].get_text(strip=True))
                except (IndexError, ValueError, TypeError):
                    total_fats = 0

                btn = tr.find("button")
                char_id = None
                if btn and btn.has_attr("data-character-id"):
                    raw_id = btn["data-character-id"]
                    try:
                        char_id = int(str(raw_id))
                    except (ValueError, TypeError):
                        char_id = None

                records.append(
                    {
                        "character_name": char_name,
                        "character_id": char_id,
                        "is_main": True,
                        "total_fats": total_fats,
                        "fat_details": {},
                        "ship_details": {},
                    }
                )
            return records

        # 2. Fallback to generic table parsing
        table = soup.find("table")
        if not table:
            return []

        headers: list[str] = []
        thead = table.find("thead")  # type: ignore[union-attr]
        if thead:
            headers = [th.get_text(strip=True) for th in thead.find_all("th")]  # type: ignore[union-attr]
        elif table.find("tr"):  # type: ignore[union-attr]
            headers = [td.get_text(strip=True) for td in table.find("tr").find_all(["th", "td"])]  # type: ignore[union-attr]

        if not headers:
            return []

        generic_records: list[dict[str, Any]] = []
        tbody = table.find("tbody") or table  # type: ignore[union-attr]
        rows = tbody.find_all("tr")  # type: ignore[union-attr]

        for tr in rows:
            cell_texts = [td.get_text(strip=True) for td in tr.find_all("td")]
            if not cell_texts or len(cell_texts) < len(headers):
                continue

            row_dict: dict[str, str] = dict(zip(headers, cell_texts))
            char_name = row_dict.get("Main Character") or row_dict.get("Character") or cell_texts[0]
            if not char_name:
                continue

            active_val = row_dict.get("Active for Corporation Tracking", "0")
            is_main = str(active_val) in {"1", "true", "True"}

            try:
                total_val = row_dict.get("Total FATs") or row_dict.get("Total") or row_dict.get("FATs", "0") or "0"
                total_fats = int(total_val)
            except (ValueError, TypeError):
                total_fats = 0

            standard_cols = {
                "main character",
                "character",
                "active for corporation tracking",
                "total fats",
                "total",
                "fats",
            }
            fat_details: dict[str, int] = {}
            for col, val in row_dict.items():
                if col.lower() not in standard_cols:
                    try:
                        fat_details[col] = int(val) if val else 0
                    except (ValueError, TypeError):
                        pass

            generic_records.append(
                {
                    "character_name": char_name,
                    "is_main": is_main,
                    "total_fats": total_fats,
                    "fat_details": fat_details,
                    "ship_details": {},
                }
            )

        return generic_records

    @staticmethod
    def parse_html_charts(html_content: str) -> tuple[dict[str, int], dict[str, int], dict[str, int]]:
        """
        Extracts 'time-line' (hours 0..23), 'weekday-line' (Monday..Sunday), and 'ship-bar-stacked'
        chart datasets from INIT Auth AFAT HTML page.
        """
        fats_by_time: dict[str, int] = {}
        fats_by_weekday: dict[str, int] = {}
        fats_by_ship: dict[str, int] = {}

        if not html_content or not html_content.strip():
            return fats_by_time, fats_by_weekday, fats_by_ship

        # 1. FATs by time (24 hours: 0-23)
        time_match = re.search(r"time-line.*?data:\s*\[([0-9,\s]+)\]", html_content, re.DOTALL)
        if time_match:
            vals = [int(x.strip()) for x in time_match.group(1).split(",") if x.strip()]
            for h in range(24):
                fats_by_time[str(h)] = vals[h] if h < len(vals) else 0

        # 2. FATs by weekday (7 days: Monday..Sunday)
        weekday_match = re.search(r"weekday-line.*?data:\s*\[([0-9,\s]+)\]", html_content, re.DOTALL)
        if weekday_match:
            vals = [int(x.strip()) for x in weekday_match.group(1).split(",") if x.strip()]
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            for idx, day in enumerate(day_names):
                fats_by_weekday[day] = vals[idx] if idx < len(vals) else 0

        # 3. FATs by ship type (ship-bar-stacked)
        ship_block_match = re.search(r"ship-bar-stacked.*?</script>", html_content, re.DOTALL)
        if ship_block_match:
            script_chunk = ship_block_match.group(0)
            ship_datasets = re.findall(
                r"label:\s*['\"]([^'\"]+)['\"],[^}]*?data:\s*\[([0-9,\s]+)\]",
                script_chunk,
            )
            for label, data_str in ship_datasets:
                clean_label = label.strip()
                if clean_label in {"# of FATs", "Total"} or not clean_label:
                    continue
                counts = [int(x.strip()) for x in data_str.split(",") if x.strip()]
                total = sum(counts)
                if total > 0:
                    fats_by_ship[clean_label] = fats_by_ship.get(clean_label, 0) + total

        return fats_by_time, fats_by_weekday, fats_by_ship

    @classmethod
    @transaction.atomic
    def ingest_records(
        cls,
        corporation_id: int,
        corporation_name: str,
        year: int,
        month: int,
        records: list[dict[str, Any]],
        synced_by: User | None = None,
        fats_by_time: dict[str, int] | None = None,
        fats_by_weekday: dict[str, int] | None = None,
        fats_by_ship: dict[str, int] | None = None,
    ) -> FatMonthPeriod:
        """
        Atomically ingests a batch of records into a specific FatMonthPeriod.
        Matches characters against local EveCharacter records when available.
        """
        period, _ = FatMonthPeriod.objects.get_or_create(
            corporation_id=corporation_id,
            year=year,
            month=month,
            defaults={
                "corporation_name": corporation_name,
                "synced_by": synced_by,
            },
        )
        period.corporation_name = corporation_name
        if synced_by:
            period.synced_by = synced_by

        # Bulk resolve EveCharacters from local Auth database
        char_names = [r["character_name"] for r in records]
        eve_chars = EveCharacter.objects.filter(character_name__in=char_names).select_related(
            "character_ownership__user__profile__main_character"
        )
        char_map = {c.character_name: c for c in eve_chars}

        # Clear existing entries for this period to guarantee clean idempotency
        period.entries.all().delete()

        entries_to_create: list[FatEntry] = []
        for rec in records:
            char_name = rec["character_name"]
            eve_char = char_map.get(char_name)
            if not eve_char and rec.get("character_id"):
                eve_char = EveCharacter.objects.filter(character_id=rec["character_id"]).first()

            main_char_id = rec.get("character_id")
            main_char_name = char_name
            is_main = rec.get("is_main", True)

            if eve_char:
                try:
                    ownership = getattr(eve_char, "character_ownership", None)
                    if ownership and ownership.user and hasattr(ownership.user, "profile"):
                        main_char = ownership.user.profile.main_character
                        if main_char:
                            main_char_id = main_char.character_id
                            main_char_name = main_char.character_name
                            is_main = main_char.character_id == eve_char.character_id
                except Exception:
                    pass

            entries_to_create.append(
                FatEntry(
                    period=period,
                    character=eve_char,
                    character_name=char_name,
                    main_character_id=main_char_id,
                    main_character_name=main_char_name,
                    is_main=is_main,
                    total_fats=rec["total_fats"],
                    ship_details=rec.get("ship_details", {}),
                    fat_details=rec.get("fat_details", {}),
                )
            )

        FatEntry.objects.bulk_create(entries_to_create)

        period.total_fats = sum(e.total_fats for e in entries_to_create)
        if fats_by_time is not None:
            period.fats_by_time = fats_by_time
        if fats_by_weekday is not None:
            period.fats_by_weekday = fats_by_weekday
        if fats_by_ship is not None:
            period.fats_by_ship = fats_by_ship
        period.save()

        # Update sync config logs if available
        try:
            config = FatSyncConfig.objects.filter(corporation_id=corporation_id).first()
            if config:
                config.last_sync_at = timezone.now()
                config.last_sync_status = "success"
                log_entry = (
                    f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Ingested {len(entries_to_create)} "
                    f"entries for {period.label} ({period.total_fats} total FATs).\n"
                )
                config.last_sync_log = (log_entry + config.last_sync_log)[:4000]
                config.save(update_fields=["last_sync_at", "last_sync_status", "last_sync_log"])
        except Exception:
            pass

        return period


class FatAggregationService:
    """
    Dynamic aggregation supporting 30d, 90d, 120d, YTD, specific years, and multi-year time windows.
    """

    @classmethod
    def get_periods_for_window(
        cls,
        corporation_id: int | None = None,
        window: str = "90d",
        year: int | None = None,
    ) -> list[FatMonthPeriod]:
        """
        Returns FatMonthPeriod instances matching the requested window, ordered chronologically.
        """
        qs = FatMonthPeriod.objects.all()
        if corporation_id:
            qs = qs.filter(corporation_id=corporation_id)

        all_periods = list(qs.order_by("-year", "-month"))
        if not all_periods:
            return []

        if window == "30d":
            matched = all_periods[:1]
        elif window == "90d":
            matched = all_periods[:3]
        elif window == "120d":
            matched = all_periods[:4]
        elif window == "ytd":
            current_year = timezone.now().year
            matched = [p for p in all_periods if p.year == current_year]
            if not matched:  # Fallback to the latest year available in data
                latest_year = all_periods[0].year
                matched = [p for p in all_periods if p.year == latest_year]
        elif window.startswith("year_"):
            try:
                target_year = int(window.split("_")[1])
                matched = [p for p in all_periods if p.year == target_year]
            except (IndexError, ValueError):
                matched = all_periods[:3]
        elif window == "all":
            matched = all_periods
        else:
            if year:
                matched = [p for p in all_periods if p.year == year]
            else:
                matched = all_periods[:3]

        # Return chronologically (oldest to newest) for charts and progressive tables
        return sorted(matched, key=lambda p: (p.year, p.month))

    @classmethod
    def aggregate_data(
        cls,
        corporation_id: int | None = None,
        window: str = "90d",
        year: int | None = None,
    ) -> dict[str, Any]:
        """
        Aggregates participant activity, dynamic FAT columns, corporation trends, and charts.
        """
        periods = cls.get_periods_for_window(corporation_id=corporation_id, window=window, year=year)

        if not periods:
            return {
                "window": window,
                "periods": [],
                "dynamic_headers": [],
                "pilots": [],
                "total_fats": 0,
                "active_pilots_count": 0,
                "total_pilots_count": 0,
                "trend_labels": [],
                "trend_values": [],
                "top_pilots_labels": [],
                "top_pilots_values": [],
                "fat_type_distribution": {},
                "ship_type_distribution": {},
                "fats_by_time_labels": [f"{h:02d}:00" for h in range(24)],
                "fats_by_time_values": [0] * 24,
                "fats_by_weekday_labels": [
                    str(_("Monday")),
                    str(_("Tuesday")),
                    str(_("Wednesday")),
                    str(_("Thursday")),
                    str(_("Friday")),
                    str(_("Saturday")),
                    str(_("Sunday")),
                ],
                "fats_by_weekday_values": [0] * 7,
            }

        period_ids = [p.id for p in periods]
        entries = (
            FatEntry.objects.filter(period_id__in=period_ids)
            .select_related("character", "period")
            .order_by("character_name")
        )

        # Collect dynamic headers across all entries in the window
        dynamic_headers_set: set[str] = set()
        for e in entries:
            dynamic_headers_set.update(e.fat_details.keys())
        dynamic_headers = sorted(list(dynamic_headers_set))

        # Group by character
        pilot_records: dict[str, dict[str, Any]] = {}
        fat_type_distribution: dict[str, int] = defaultdict(int)

        for e in entries:
            name = e.character_name
            if name not in pilot_records:
                pilot_records[name] = {
                    "character_name": name,
                    "character_id": e.character.character_id if e.character else None,
                    "main_character_name": e.main_character_name or name,
                    "is_main": e.is_main,
                    "total_fats": 0,
                    "period_fats": {p.id: 0 for p in periods},
                    "fat_details": {h: 0 for h in dynamic_headers},
                    "active_months": 0,
                }

            pilot_records[name]["total_fats"] += e.total_fats
            pilot_records[name]["period_fats"][e.period_id] += e.total_fats
            if e.total_fats > 0:
                pilot_records[name]["active_months"] += 1

            for h, count in e.fat_details.items():
                if h in pilot_records[name]["fat_details"]:
                    pilot_records[name]["fat_details"][h] += count
                fat_type_distribution[h] += count

        # Convert to list and compute dynamic values list per pilot for template DataTables
        pilot_list = list(pilot_records.values())
        for p in pilot_list:
            p["dynamic_values"] = [p["fat_details"].get(h, 0) for h in dynamic_headers]
            p["period_values"] = [p["period_fats"].get(period.id, 0) for period in periods]
            p["avg_fats_per_month"] = round(p["total_fats"] / len(periods), 1) if periods else 0

        # Sort pilots by total FATs descending
        pilot_list.sort(key=lambda x: x["total_fats"], reverse=True)

        # Chart Data: Monthly Trends
        trend_labels = [p.label for p in periods]
        trend_values = [p.total_fats for p in periods]

        top_10 = pilot_list[:10]
        top_pilots_labels = [p["character_name"] for p in top_10]
        top_pilots_values = [p["total_fats"] for p in top_10]

        total_fats = sum(p.total_fats for p in periods)
        active_pilots_count = sum(1 for p in pilot_list if p["total_fats"] > 0)
        total_pilots_count = len(pilot_list)

        # Chart Data: Hourly Distribution (00:00 - 23:00)
        time_counts: dict[str, int] = {str(h): 0 for h in range(24)}
        for period in periods:
            if period.fats_by_time and isinstance(period.fats_by_time, dict):
                for h_str, val in period.fats_by_time.items():
                    if h_str in time_counts:
                        try:
                            time_counts[h_str] += int(val)
                        except (ValueError, TypeError):
                            pass

        fats_by_time_labels = [f"{h:02d}:00" for h in range(24)]
        fats_by_time_values = [time_counts[str(h)] for h in range(24)]

        # Chart Data: Weekday Distribution (Monday - Sunday)
        raw_weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday_display_names = [
            _("Monday"),
            _("Tuesday"),
            _("Wednesday"),
            _("Thursday"),
            _("Friday"),
            _("Saturday"),
            _("Sunday"),
        ]
        weekday_counts: dict[str, int] = {d: 0 for d in raw_weekday_names}
        for period in periods:
            if period.fats_by_weekday and isinstance(period.fats_by_weekday, dict):
                for d_str, val in period.fats_by_weekday.items():
                    if d_str in weekday_counts:
                        try:
                            weekday_counts[d_str] += int(val)
                        except (ValueError, TypeError):
                            pass

        fats_by_weekday_labels = [str(w) for w in weekday_display_names]
        fats_by_weekday_values = [weekday_counts[d] for d in raw_weekday_names]

        # Chart Data: Ship Distribution across active periods (Top 12 + Other Ships)
        raw_ship_counts: dict[str, int] = defaultdict(int)
        for period in periods:
            if period.fats_by_ship and isinstance(period.fats_by_ship, dict):
                for ship_name, count in period.fats_by_ship.items():
                    try:
                        c = int(count)
                        if c > 0:
                            raw_ship_counts[ship_name] += c
                    except (ValueError, TypeError):
                        pass

        sorted_ships = sorted(raw_ship_counts.items(), key=lambda x: x[1], reverse=True)
        ship_type_distribution: dict[str, int] = {}
        if sorted_ships:
            top_ships = sorted_ships[:12]
            for ship, count in top_ships:
                ship_type_distribution[ship] = count
            other_ships_count = sum(c for _, c in sorted_ships[12:])
            if other_ships_count > 0:
                ship_type_distribution[str(_("Other Ships"))] = other_ships_count

        return {
            "window": window,
            "periods": periods,
            "dynamic_headers": dynamic_headers,
            "pilots": pilot_list,
            "total_fats": total_fats,
            "active_pilots_count": active_pilots_count,
            "total_pilots_count": total_pilots_count,
            "trend_labels": trend_labels,
            "trend_values": trend_values,
            "top_pilots_labels": top_pilots_labels,
            "top_pilots_values": top_pilots_values,
            "fat_type_distribution": dict(fat_type_distribution),
            "ship_type_distribution": ship_type_distribution,
            "fats_by_time_labels": fats_by_time_labels,
            "fats_by_time_values": fats_by_time_values,
            "fats_by_weekday_labels": fats_by_weekday_labels,
            "fats_by_weekday_values": fats_by_weekday_values,
        }
