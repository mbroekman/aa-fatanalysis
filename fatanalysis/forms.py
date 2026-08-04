from django import forms

class CsvImportForm(forms.Form):
    PERIOD_CHOICES = (
        (30, '30 Days'),
        (90, '90 Days'),
    )
    csv_file = forms.FileField(label='FAT CSV File')
    period_type = forms.ChoiceField(choices=PERIOD_CHOICES, label='Period Type')
    custom_date = forms.DateTimeField(
        required=False,
        label='Custom Date (Optional)',
        help_text='Leave empty to use current date and time. Use format YYYY-MM-DD HH:MM if your browser does not show a date picker.',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
