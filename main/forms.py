from django import forms
from django.conf import settings


class SubmissionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        software = settings.SOFTWARE["gaussian16"]
        for name, desc in software["input_files"]["required"].items():
            self.fields[name] = forms.FileField(label=desc)
