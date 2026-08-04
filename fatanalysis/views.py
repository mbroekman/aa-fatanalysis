import csv
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.utils.translation import gettext_lazy as _

from allianceauth.eveonline.models import EveCharacter
from .forms import CsvImportForm
from .models import UploadPeriod, FatEntry

@login_required
@permission_required('fatanalysis.basic_access')
def index(request):
    from django.db.models import Sum

    # Data for the Trend Chart
    all_periods = UploadPeriod.objects.all().order_by('upload_date')
    trend_data = {}
    
    for period in all_periods:
        # Use period ID in the key to ensure uniqueness if multiple uploads happen on the same day
        date_str = f"{period.upload_date.strftime('%Y-%m-%d')} (ID:{period.id})"
        if date_str not in trend_data:
            trend_data[date_str] = {30: 0, 90: 0}
            
        # Get total fats for this period
        total_fats = FatEntry.objects.filter(period=period).aggregate(Sum('total_fats'))['total_fats__sum'] or 0
        
        trend_data[date_str][period.period_type] += total_fats

    trend_labels = list(trend_data.keys())
    trend_30 = [trend_data[d][30] for d in trend_labels]
    trend_90 = [trend_data[d][90] for d in trend_labels]

    # Data for the 30-Day and 90-Day tables (Removed from index)
    
    context = {
        'trend_labels': trend_labels,
        'trend_30': trend_30,
        'trend_90': trend_90,
    }
    return render(request, 'fatanalysis/index.html', context)

@login_required
@permission_required('fatanalysis.basic_access')
def overview_30(request):
    latest_30 = UploadPeriod.objects.filter(period_type=30).order_by('-upload_date').first()
    entries = FatEntry.objects.filter(period=latest_30) if latest_30 else []
    
    player_data = []
    dynamic_headers_set = set()
    if entries:
        for entry in entries:
            dynamic_headers_set.update(entry.fat_details.keys())
            
    dynamic_headers = sorted(list(dynamic_headers_set))
    
    enriched_entries = []
    if entries:
        for entry in entries:
            player_data.append({'name': entry.character_name, 'fats': entry.total_fats})
            
            row_details = []
            for header in dynamic_headers:
                row_details.append(entry.fat_details.get(header, 0))
            
            entry.dynamic_values = row_details
            enriched_entries.append(entry)
            
        player_data = sorted(player_data, key=lambda x: x['fats'], reverse=True)[:10]

    all_30 = UploadPeriod.objects.filter(period_type=30).order_by('upload_date')
    trend_labels = []
    trend_data = []
    for p in all_30:
        trend_labels.append(f"{p.upload_date.strftime('%Y-%m-%d')} (ID:{p.id})")
        total = FatEntry.objects.filter(period=p).aggregate(Sum('total_fats'))['total_fats__sum'] or 0
        trend_data.append(total)

    context = {
        'title': _('Latest 30 Days FATs Overview'),
        'period': latest_30,
        'entries': enriched_entries,
        'dynamic_headers': dynamic_headers,
        'top_labels': [p['name'] for p in player_data],
        'top_data': [p['fats'] for p in player_data],
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'period_type': 30,
    }
    return render(request, 'fatanalysis/overview.html', context)

@login_required
@permission_required('fatanalysis.basic_access')
def overview_90(request):
    latest_90 = UploadPeriod.objects.filter(period_type=90).order_by('-upload_date').first()
    entries = FatEntry.objects.filter(period=latest_90) if latest_90 else []
    
    player_data = []
    dynamic_headers_set = set()
    if entries:
        for entry in entries:
            dynamic_headers_set.update(entry.fat_details.keys())
            
    dynamic_headers = sorted(list(dynamic_headers_set))
    
    enriched_entries = []
    if entries:
        for entry in entries:
            player_data.append({'name': entry.character_name, 'fats': entry.total_fats})
            
            row_details = []
            for header in dynamic_headers:
                row_details.append(entry.fat_details.get(header, 0))
            
            entry.dynamic_values = row_details
            enriched_entries.append(entry)
            
        player_data = sorted(player_data, key=lambda x: x['fats'], reverse=True)[:10]

    all_90 = UploadPeriod.objects.filter(period_type=90).order_by('upload_date')
    trend_labels = []
    trend_data = []
    for p in all_90:
        trend_labels.append(f"{p.upload_date.strftime('%Y-%m-%d')} (ID:{p.id})")
        total = FatEntry.objects.filter(period=p).aggregate(Sum('total_fats'))['total_fats__sum'] or 0
        trend_data.append(total)

    context = {
        'title': _('Latest 90 Days FATs Overview'),
        'period': latest_90,
        'entries': enriched_entries,
        'dynamic_headers': dynamic_headers,
        'top_labels': [p['name'] for p in player_data],
        'top_data': [p['fats'] for p in player_data],
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'period_type': 90,
    }
    return render(request, 'fatanalysis/overview.html', context)

@login_required
@permission_required('fatanalysis.basic_access')
def import_csv(request):
    if request.method == 'POST':
        form = CsvImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            period_type = int(form.cleaned_data['period_type'])
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, _("Please upload a valid CSV file."))
                return redirect('fatanalysis:import_csv')
            
            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                with transaction.atomic():
                    # Create Upload Period
                    kwargs = {
                        'uploader': request.user.username,
                        'period_type': period_type
                    }
                    if form.cleaned_data.get('custom_date'):
                        kwargs['upload_date'] = form.cleaned_data['custom_date']
                    upload_period = UploadPeriod.objects.create(**kwargs)
                    
                    entries_to_create = []
                    
                    for row in reader:
                        char_name = row.get('Main Character', '').strip()
                        if not char_name:
                            continue
                            
                        # Try to find character in DB
                        eve_char = EveCharacter.objects.filter(character_name=char_name).first()
                        
                        try:
                            total_fats = int(row.get('Total FATs', 0))
                        except ValueError:
                            total_fats = 0
                        
                        # Get all other columns as details
                        details = {}
                        standard_keys = ['Main Character', 'Total FATs']
                        for key, value in row.items():
                            if key not in standard_keys:
                                try:
                                    details[key] = int(value) if value else 0
                                except ValueError:
                                    details[key] = value

                        entries_to_create.append(
                            FatEntry(
                                period=upload_period,
                                character=eve_char,
                                character_name=char_name,
                                total_fats=total_fats,
                                fat_details=details
                            )
                        )
                    
                    FatEntry.objects.bulk_create(entries_to_create)
                    messages.success(request, _(f"Successfully imported {len(entries_to_create)} FAT entries."))
                    return redirect('fatanalysis:period_detail', period_id=upload_period.id)
                    
            except Exception as e:
                messages.error(request, _(f"Error parsing CSV: {e}"))
                return redirect('fatanalysis:import_csv')
                
    else:
        form = CsvImportForm()
        
    return render(request, 'fatanalysis/import_csv.html', {'form': form})

@login_required
@permission_required('fatanalysis.basic_access')
def period_detail(request, period_id):
    from django.shortcuts import get_object_or_404
    from django.db.models import Sum

    period = get_object_or_404(UploadPeriod, id=period_id)
    entries = FatEntry.objects.filter(period=period).select_related('character')
    
    # Aggregations for charts
    player_data = []
    
    # Collect dynamic headers
    dynamic_headers_set = set()
    for entry in entries:
        dynamic_headers_set.update(entry.fat_details.keys())
        
    # Sort headers to ensure consistent column ordering
    dynamic_headers = sorted(list(dynamic_headers_set))
    
    # Create enriched entries for template rendering
    enriched_entries = []
    for entry in entries:
        player_data.append({
            'name': entry.character_name,
            'fats': entry.total_fats
        })
        
        row_details = []
        for header in dynamic_headers:
            row_details.append(entry.fat_details.get(header, 0))
            
        enriched_entries.append({
            'character_name': entry.character_name,
            'total_fats': entry.total_fats,
            'dynamic_values': row_details
        })
        
    # Sort for charts
    player_data = sorted(player_data, key=lambda x: x['fats'], reverse=True)[:20] # Top 20 players
    
    player_labels = [p['name'] for p in player_data]
    player_values = [p['fats'] for p in player_data]

    context = {
        'period': period,
        'entries': enriched_entries,
        'dynamic_headers': dynamic_headers,
        'player_labels': player_labels,
        'player_values': player_values,
    }
    return render(request, 'fatanalysis/period_detail.html', context)

@login_required
@permission_required('fatanalysis.basic_access')
def period_list(request):
    periods = UploadPeriod.objects.all().order_by('-upload_date')
    return render(request, 'fatanalysis/period_list.html', {'periods': periods})

@login_required
@permission_required('fatanalysis.basic_access')
def period_delete(request, period_id):
    from django.shortcuts import get_object_or_404
    period = get_object_or_404(UploadPeriod, id=period_id)
    if request.method == 'POST':
        period.delete()
        messages.success(request, _("Upload period and all associated data deleted successfully."))
        return redirect('fatanalysis:period_list')
    return render(request, 'fatanalysis/period_delete.html', {'period': period})


@login_required
@permission_required('fatanalysis.basic_access')
def player_detail(request, character_name, period_type):
    from collections import defaultdict
    # Get all entries for this character and period type, chronologically
    periods = UploadPeriod.objects.filter(period_type=period_type).order_by('upload_date')
    entries = FatEntry.objects.filter(character_name=character_name, period__period_type=period_type).select_related('period').order_by('period__upload_date')
    
    if not entries:
        messages.warning(request, _(f"No data found for {character_name}."))
        return redirect('fatanalysis:index')

    dynamic_headers_set = set()
    for entry in entries:
        dynamic_headers_set.update(entry.fat_details.keys())
    dynamic_headers = sorted(list(dynamic_headers_set))

    # Prepare Line Chart Data (Trend per FAT type)
    trend_labels = []
    trend_datasets_dict = defaultdict(list)
    total_fats_trend = []
    
    # We want a data point for ALL periods of this type, even if the player had 0
    # Create a lookup for player entries
    entry_lookup = {e.period.id: e for e in entries}

    for p in periods:
        trend_labels.append(f"{p.upload_date.strftime('%Y-%m-%d')} (ID:{p.id})")
        
        entry = entry_lookup.get(p.id)
        if entry:
            total_fats_trend.append(entry.total_fats)
            for header in dynamic_headers:
                trend_datasets_dict[header].append(entry.fat_details.get(header, 0))
        else:
            total_fats_trend.append(0)
            for header in dynamic_headers:
                trend_datasets_dict[header].append(0)

    # Convert datasets to Chart.js format
    trend_datasets = []
    colors = ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40', '#E7E9ED', '#8AC926', '#1982C4', '#6A4C93']
    for i, header in enumerate(dynamic_headers):
        trend_datasets.append({
            'label': header,
            'data': trend_datasets_dict[header],
            'borderColor': colors[i % len(colors)],
            'tension': 0.1,
            'fill': False,
            'hidden': False
        })
    # Add Total line
    trend_datasets.append({
        'label': 'Total FATs',
        'data': total_fats_trend,
        'borderColor': '#000000',
        'borderDash': [5, 5],
        'tension': 0.1,
        'fill': False
    })

    # Prepare Pie Chart Data (Latest Period Distribution)
    latest_entry = entries.last()
    pie_labels = []
    pie_data = []
    if latest_entry:
        for header in dynamic_headers:
            val = latest_entry.fat_details.get(header, 0)
            if val > 0:
                pie_labels.append(header)
                pie_data.append(val)

    context = {
        'title': _(f"Player Detail: {character_name}"),
        'character_name': character_name,
        'period_type': period_type,
        'entries': entries,
        'dynamic_headers': dynamic_headers,
        'trend_labels': trend_labels,
        'trend_datasets': trend_datasets,
        'pie_labels': pie_labels,
        'pie_data': pie_data,
        'latest_period': latest_entry.period if latest_entry else None,
    }
    return render(request, 'fatanalysis/player_detail.html', context)
