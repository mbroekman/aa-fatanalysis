import calendar
from datetime import datetime

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


class FatDirectCsvForm(forms.Form):
    """
    Form for directly uploading or pasting an AFAT CSV into a designated month/year.
    """

    current_year = timezone.now().year
    YEAR_CHOICES = [(y, str(y)) for y in range(current_year - 5, current_year + 2)]
    MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]

    year = forms.ChoiceField(
        choices=YEAR_CHOICES,
        initial=current_year,
        label=_("Year"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    month = forms.ChoiceField(
        choices=MONTH_CHOICES,
        initial=datetime.now().month,
        label=_("Month"),
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    corporation_name = forms.CharField(
        max_length=255,
        initial="Game of Drones",
        label=_("Corporation Name"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    csv_file = forms.FileField(
        required=False,
        label=_("Upload CSV File"),
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": ".csv,text/csv"}),
    )
    csv_text = forms.CharField(
        required=False,
        label=_("Or Paste CSV Text"),
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 4, "placeholder": "Main Character,Total FATs..."}
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        csv_file = cleaned_data.get("csv_file")
        csv_text = cleaned_data.get("csv_text")

        if not csv_file and not (csv_text and csv_text.strip()):
            raise forms.ValidationError(_("Please either upload a CSV file or paste CSV text."))
        return cleaned_data
