from django import forms

from .models import Job, Project
from .resources import RESOURCE_CHOICES
from .software import SOFTWARE_CHOICES


class SubmissionForm(forms.Form):
    def __init__(self, software, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"] = forms.CharField(
            max_length=200, label="Description", required=False
        )
        for name, label in software["input_files"]["required"].items():
            self.fields[name] = forms.FileField(label=label, label_suffix=" (*)")
        for name, label in software["input_files"]["optional"].items():
            self.fields[name] = forms.FileField(label=label, required=False)


class JobTypeForm(forms.Form):
    project = forms.ModelChoiceField(
        Project.objects.all(), label="Project", label_suffix=" (*)", empty_label=None
    )
    resources = forms.ChoiceField(
        label="Job Resources",
        choices=RESOURCE_CHOICES,
        label_suffix=" (*)",
    )
    software = forms.ChoiceField(
        label="Software",
        choices=SOFTWARE_CHOICES,
        label_suffix=" (*)",
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = "__all__"


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["description", "project"]
