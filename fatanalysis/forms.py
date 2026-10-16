import calendar

from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import FatSyncConfig


class FatSyncConfigForm(forms.ModelForm):
    """
    Form for directors to configure AFAT scraper credentials and endpoints.
    """

    session_cookie = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 2, "placeholder": "sessionid cookie value from INIT Auth"}),
        label=_("Session Cookie (sessionid)"),
        help_text=_("The active sessionid cookie from the source Alliance Auth instance."),
    )

    class Meta:
        model = FatSyncConfig
        fields = [
            "corporation_id",
            "corporation_name",
            "source_url",
            "session_cookie",
            "user_agent",
        ]
        widgets = {
            "corporation_id": forms.NumberInput(attrs={"class": "form-control"}),
            "corporation_name": forms.TextInput(attrs={"class": "form-control"}),
            "source_url": forms.URLInput(attrs={"class": "form-control"}),
            "user_agent": forms.TextInput(attrs={"class": "form-control"}),
        }


class FatSyncSingleMonthForm(forms.Form):
    """
    Form for fetching a specific month's AFAT statistics directly from INIT Auth.
    """

    current_year = timezone.now().year
    YEAR_CHOICES = [(y, str(y)) for y in range(current_year - 5, current_year + 1)]
    MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]

    year = forms.IntegerField(
        initial=current_year,
        label=_("Year"),
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 2018, "max": current_year + 1}),
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        initial=timezone.now().month,
        label=_("Month"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class FatSyncBulkForm(forms.Form):
    """
    Form for initiating a bulk crawler sync across all historical periods.
    """

    current_year = timezone.now().year
    current_month = timezone.now().month
    MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]

    start_year = forms.IntegerField(
        initial=2024,
        label=_("Start Year"),
        help_text=_("The earliest year to begin crawling from (e.g. 2024)."),
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 2018, "max": current_year}),
    )
    end_year = forms.IntegerField(
        initial=current_year,
        label=_("End Year"),
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 2018, "max": current_year + 1}),
    )
    end_month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        initial=current_month,
        label=_("End Month"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
