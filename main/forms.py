from django import forms
from django.conf import settings

from .models import Job, Project


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


class JobTypeForm(forms.Form):
    project = forms.ModelChoiceField(
        Project.objects.all(), label="Project", label_suffix=" (*)"
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = "__all__"


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["description", "project"]
