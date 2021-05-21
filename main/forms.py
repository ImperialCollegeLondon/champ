from django import forms
from django.conf import settings


class SubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        software = settings.SOFTWARE["gaussian16"]
        self.fields["description"] = forms.CharField(
            max_length=200, label="Description", required=False
        )
        for name, label in software["input_files"]["required"].items():
            self.fields[name] = forms.FileField(label=label, label_suffix=" (*)")
        for name, label in software["input_files"]["optional"].items():
            self.fields[name] = forms.FileField(label=label, required=False)
