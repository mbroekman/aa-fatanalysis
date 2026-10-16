"""
Views for aa-fatanalysis:
- Main Dashboard with dynamic time windows (30d, 90d, 120d, YTD, Multi-Year)
- Player Detail with longitudinal FAT trends and breakdown
- Director Sync & Ingestion Management (Scraper config, Connection testing, Direct CSV import)
- Period list, detail, and deletion
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .forms import FatSyncBulkForm, FatSyncConfigForm, FatSyncSingleMonthForm
from .models import FatEntry, FatMonthPeriod, FatSyncConfig
from .services import AfatScraperService, FatAggregationService, FatIngestionService

logger = logging.getLogger(__name__)


@login_required
@permission_required("fatanalysis.basic_access", raise_exception=True)
def index(request: HttpRequest) -> HttpResponse:
    """
    Main FAT Analysis dashboard with dynamic time window filtering.
    """
    window = request.GET.get("window", "90d")
    config = FatSyncConfig.get_solo()

    # Determine available years for filter pills.
    # Clearing order_by avoids implicit Meta ordering columns in SELECT DISTINCT.
    available_years = sorted(
        list(
            set(
                FatMonthPeriod.objects.filter(corporation_id=config.corporation_id)
                .order_by()
                .values_list("year", flat=True)
                .distinct()
            )
        ),
        reverse=True,
    )
    if not available_years:
        available_years = [timezone.now().year]

    agg_data = FatAggregationService.aggregate_data(
        corporation_id=config.corporation_id,
        window=window,
    )

    context = {
        "title": _("FAT Analysis Dashboard"),
        "window": window,
        "available_years": available_years,
        "config": config,
        "agg": agg_data,
        "periods": agg_data["periods"],
        "dynamic_headers": agg_data["dynamic_headers"],
        "pilots": agg_data["pilots"],
        "total_fats": agg_data["total_fats"],
        "active_pilots_count": agg_data["active_pilots_count"],
        "total_pilots_count": agg_data["total_pilots_count"],
        "trend_labels": agg_data["trend_labels"],
        "trend_values": agg_data["trend_values"],
        "top_pilots_labels": agg_data["top_pilots_labels"],
        "top_pilots_values": agg_data["top_pilots_values"],
        "fat_type_distribution": agg_data["fat_type_distribution"],
        "ship_type_distribution": agg_data["ship_type_distribution"],
        "fats_by_time_labels": agg_data["fats_by_time_labels"],
        "fats_by_time_values": agg_data["fats_by_time_values"],
        "fats_by_weekday_labels": agg_data["fats_by_weekday_labels"],
        "fats_by_weekday_values": agg_data["fats_by_weekday_values"],
        "has_time_data": any(v > 0 for v in agg_data["fats_by_time_values"]),
        "has_weekday_data": any(v > 0 for v in agg_data["fats_by_weekday_values"]),
        "table_columns_count": 5 + len(agg_data["periods"]) + len(agg_data["dynamic_headers"]),
    }
    return render(request, "fatanalysis/index.html", context)


@login_required
@permission_required("fatanalysis.basic_access", raise_exception=True)
def player_detail(request: HttpRequest, character_name: str) -> HttpResponse:
    """
    Detailed longitudinal view of an individual pilot's FAT participation over all recorded periods.
    """
    entries = (
        FatEntry.objects.filter(character_name=character_name)
        .select_related("period", "character")
        .order_by("period__year", "period__month")
    )

    if not entries.exists():
        messages.warning(request, _("No FAT participation data found for %(pilot)s.") % {"pilot": character_name})
        return redirect("fatanalysis:index")

    # Collect dynamic headers for this player
    dynamic_headers_set: set[str] = set()
    fat_type_totals: dict[str, int] = {}
    for entry in entries:
        for k, v in entry.fat_details.items():
            dynamic_headers_set.add(k)
            fat_type_totals[k] = fat_type_totals.get(k, 0) + v

    dynamic_headers = sorted(list(dynamic_headers_set))

    # Prepare enriched entries and trend charts
    trend_labels = []
    trend_totals = []
    for entry in entries:
        trend_labels.append(entry.period.label)
        trend_totals.append(entry.total_fats)
        setattr(entry, "dynamic_values", [entry.fat_details.get(h, 0) for h in dynamic_headers])

    first_entry = entries.first()
    latest_entry = entries.last()
    total_fats_sum = sum(e.total_fats for e in entries)
    active_periods_count = sum(1 for e in entries if e.total_fats > 0)

    # Pie/Doughnut chart for FAT types
    pie_labels = [k for k, v in fat_type_totals.items() if v > 0]
    pie_values = [v for v in fat_type_totals.values() if v > 0]

    context = {
        "title": _("Pilot FAT Detail: %(name)s") % {"name": character_name},
        "character_name": character_name,
        "first_entry": first_entry,
        "latest_entry": latest_entry,
        "entries": entries,
        "dynamic_headers": dynamic_headers,
        "total_fats": total_fats_sum,
        "active_periods_count": active_periods_count,
        "total_periods_count": entries.count(),
        "trend_labels": trend_labels,
        "trend_totals": trend_totals,
        "pie_labels": pie_labels,
        "pie_values": pie_values,
    }
    return render(request, "fatanalysis/player_detail.html", context)


@login_required
@permission_required("fatanalysis.manage_fatanalysis", raise_exception=True)
def sync_management(request: HttpRequest) -> HttpResponse:
    """
    Director view for managing AFAT scraper config, testing connections, and syncing reports from INIT Auth.
    """
    config = FatSyncConfig.get_solo()
    config_form = FatSyncConfigForm(instance=config)
    month_form = FatSyncSingleMonthForm()
    bulk_form = FatSyncBulkForm()

    if request.method == "POST":
        action = request.POST.get("action", "")

        # Action 1: Save Configuration
        if action == "save_config":
            config_form = FatSyncConfigForm(request.POST, instance=config)
            if config_form.is_valid():
                config_form.save()
                messages.success(request, _("AFAT sync configuration updated successfully."))
                return redirect("fatanalysis:sync_management")

        # Action 2: Test Connection
        elif action == "test_connection":
            config_form = FatSyncConfigForm(request.POST, instance=config)
            if config_form.is_valid():
                config = config_form.save()
                scraper = AfatScraperService(config=config)
                success, msg = scraper.test_connection()
                if success:
                    messages.success(request, msg)
                else:
                    messages.error(request, msg)
                return redirect("fatanalysis:sync_management")

        # Action 3: Sync Single Month from INIT Auth
        elif action == "sync_single_month":
            month_form = FatSyncSingleMonthForm(request.POST)
            if month_form.is_valid():
                year = int(month_form.cleaned_data["year"])
                month = int(month_form.cleaned_data["month"])
                scraper = AfatScraperService(config=config)
                try:
                    html_content = scraper.fetch_month_report(year, month)
                    records = FatIngestionService.parse_html_table(html_content)
                    fats_by_time, fats_by_weekday, fats_by_ship = FatIngestionService.parse_html_charts(html_content)
                    if not records and not fats_by_time and not fats_by_weekday and not fats_by_ship:
                        messages.warning(
                            request,
                            _("No pilot records found on INIT Auth for %(month)s/%(year)s.")
                            % {"month": month, "year": year},
                        )
                        return redirect("fatanalysis:sync_management")

                    period = FatIngestionService.ingest_records(
                        corporation_id=config.corporation_id,
                        corporation_name=config.corporation_name,
                        year=year,
                        month=month,
                        records=records,
                        synced_by=request.user if isinstance(request.user, User) else None,
                        fats_by_time=fats_by_time,
                        fats_by_weekday=fats_by_weekday,
                        fats_by_ship=fats_by_ship,
                    )
                    messages.success(
                        request,
                        _("Successfully fetched and ingested %(count)s records for %(period)s (%(total)s total FATs).")
                        % {"count": len(records), "period": period.label, "total": period.total_fats},
                    )
                    return redirect("fatanalysis:period_detail", period_id=period.id)
                except Exception as e:
                    logger.exception("Scraper fetch error for single month: %s", e)
                    messages.error(request, _("Scraper error: %(err)s") % {"err": str(e)})
                    return redirect("fatanalysis:sync_management")

        # Action 4: Initial Bulk Sync / Historical Crawl
        elif action == "sync_bulk_history":
            bulk_form = FatSyncBulkForm(request.POST)
            if bulk_form.is_valid():
                start_year = int(bulk_form.cleaned_data["start_year"])
                end_year = int(bulk_form.cleaned_data["end_year"])
                end_month = int(bulk_form.cleaned_data["end_month"])

                scraper = AfatScraperService(config=config)
                try:
                    summary = scraper.crawl_all_periods(
                        start_year=start_year,
                        end_year=end_year,
                        end_month=end_month,
                        synced_by=request.user if isinstance(request.user, User) else None,
                    )
                    messages.success(
                        request,
                        _(
                            "Initial bulk sync completed: %(ingested)s monthly periods ingested "
                            "(%(total)s total FATs), %(skipped)s skipped without records."
                        )
                        % {
                            "ingested": summary["ingested_periods"],
                            "total": summary["total_fats"],
                            "skipped": summary["skipped_periods"],
                        },
                    )
                    return redirect("fatanalysis:index")
                except Exception as e:
                    logger.exception("Bulk sync crawler error: %s", e)
                    messages.error(request, _("Bulk sync error: %(err)s") % {"err": str(e)})
                    return redirect("fatanalysis:sync_management")

        # Action 5: Clear Sync Log
        elif action == "clear_log":
            config.last_sync_log = ""
            config.save(update_fields=["last_sync_log"])
            messages.info(request, _("Sync log cleared."))
            return redirect("fatanalysis:sync_management")

    # List of all available periods
    periods = FatMonthPeriod.objects.filter(corporation_id=config.corporation_id).order_by("-year", "-month")

    context = {
        "title": _("FAT Sync & Ingestion Management"),
        "config": config,
        "config_form": config_form,
        "month_form": month_form,
        "bulk_form": bulk_form,
        "periods": periods,
    }
    return render(request, "fatanalysis/sync_management.html", context)


@login_required
@permission_required("fatanalysis.basic_access", raise_exception=True)
def period_detail(request: HttpRequest, period_id: int) -> HttpResponse:
    """
    Detailed view of a single monthly recording period.
    """
    period = get_object_or_404(FatMonthPeriod, id=period_id)
    entries = period.entries.select_related("character").order_by("-total_fats", "character_name")

    dynamic_headers_set: set[str] = set()
    for entry in entries:
        dynamic_headers_set.update(entry.fat_details.keys())
    dynamic_headers = sorted(list(dynamic_headers_set))

    for entry in entries:
        setattr(entry, "dynamic_values", [entry.fat_details.get(h, 0) for h in dynamic_headers])

    top_entries = entries[:15]
    top_labels = [e.character_name for e in top_entries]
    top_values = [e.total_fats for e in top_entries]

    fats_by_time_labels = [f"{h:02d}:00" for h in range(24)]
    fats_by_time_values = (
        [int(period.fats_by_time.get(str(h), 0)) for h in range(24)] if period.fats_by_time else [0] * 24
    )
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
    fats_by_weekday_labels = [str(w) for w in weekday_display_names]
    fats_by_weekday_values = (
        [int(period.fats_by_weekday.get(d, 0)) for d in raw_weekday_names] if period.fats_by_weekday else [0] * 7
    )
    ship_type_distribution: dict[str, int] = {}
    if period.fats_by_ship and isinstance(period.fats_by_ship, dict):
        sorted_ships = sorted(
            [(k, int(v)) for k, v in period.fats_by_ship.items() if int(v) > 0],
            key=lambda x: x[1],
            reverse=True,
        )
        if sorted_ships:
            for ship, count in sorted_ships[:12]:
                ship_type_distribution[ship] = count
            other_ships_count = sum(c for _, c in sorted_ships[12:])
            if other_ships_count > 0:
                ship_type_distribution[str(_("Other Ships"))] = other_ships_count

    context = {
        "title": _("Monthly Period: %(period)s") % {"period": period.label},
        "period": period,
        "entries": entries,
        "dynamic_headers": dynamic_headers,
        "top_labels": top_labels,
        "top_values": top_values,
        "ship_type_distribution": ship_type_distribution,
        "fats_by_time_labels": fats_by_time_labels,
        "fats_by_time_values": fats_by_time_values,
        "fats_by_weekday_labels": fats_by_weekday_labels,
        "fats_by_weekday_values": fats_by_weekday_values,
        "has_time_data": any(v > 0 for v in fats_by_time_values),
        "has_weekday_data": any(v > 0 for v in fats_by_weekday_values),
    }
    return render(request, "fatanalysis/period_detail.html", context)


@login_required
@permission_required("fatanalysis.basic_access", raise_exception=True)
def period_list(request: HttpRequest) -> HttpResponse:
    """
    List of all monthly FAT recording periods.
    """
    config = FatSyncConfig.get_solo()
    periods = FatMonthPeriod.objects.filter(corporation_id=config.corporation_id).order_by("-year", "-month")
    return render(request, "fatanalysis/period_list.html", {"periods": periods, "title": _("Recorded FAT Periods")})


@login_required
@permission_required("fatanalysis.manage_fatanalysis", raise_exception=True)
def period_delete(request: HttpRequest, period_id: int) -> HttpResponse:
    """
    Deletes a monthly FAT recording period and all associated entries.
    """
    period = get_object_or_404(FatMonthPeriod, id=period_id)
    if request.method == "POST":
        label = period.label
        period.delete()
        messages.success(request, _("Period %(label)s and all associated entries deleted.") % {"label": label})
        return redirect("fatanalysis:period_list")
    return render(request, "fatanalysis/period_delete.html", {"period": period})


# Legacy backward compatibility views
def overview_legacy(request: HttpRequest, days: int) -> HttpResponse:
    target_window = "30d" if days <= 30 else "90d"
    return redirect(f"/fatanalysis/?window={target_window}")


def player_detail_legacy(request: HttpRequest, character_name: str, period_type: int) -> HttpResponse:
    return redirect("fatanalysis:player_detail", character_name=character_name)
