from django import forms

from .models import CustomConfig, CustomResource, Job, Profile, Project
from .resources import get_resource_choices
from .software import SOFTWARE_CHOICES


class SubmissionForm(forms.Form):
    required_css_class = "required"

    def __init__(self, software, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["description"] = forms.CharField(
            max_length=200, label="Description", required=False
        )
        for name, label in software["input_files"]["required"].items():
            self.fields[name] = forms.FileField(label=label)
        for name, label in software["input_files"]["optional"].items():
            self.fields[name] = forms.FileField(label=label, required=False)


class JobTypeForm(forms.Form):
    required_css_class = "required"
    project = forms.ModelChoiceField(
        Project.objects.all(),
        label="Project",
        empty_label=None,
    )
    resources = forms.ChoiceField(
        label="Job Resources",
        choices=get_resource_choices,
    )
    software = forms.ChoiceField(
        label="Software",
        choices=SOFTWARE_CHOICES,
    )
    custom_config = forms.ModelChoiceField(
        CustomConfig.objects.all(),
        label="Custom Configuration",
        to_field_name="label",
        required=False,
    )


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = "__all__"


class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ["description", "project"]


class CustomConfigForm(forms.ModelForm):
    class Meta:
        model = CustomConfig
        fields = "__all__"
        help_texts = {
            "script_lines": "Lines placed here are used as scheduler directives for new jobs. Resource specifications may not be provided here and will not be honoured."  # noqa: E501
        }


class CustomResourceForm(forms.ModelForm):
    class Meta:
        model = CustomResource
        fields = "__all__"
        help_texts = {
            "script_lines": "Lines should be valid scheduler directives that specify job resource requirements. Other lines may also be necessary e.g. setting environment variables. It is strongly suggested that you use a system resource configuration as a reference..",  # noqa: E501
            "label": "When a job is run using this resource configuration only the label is recorded. Therefore it is important that you provide a label that is clear and descriptive of the resources used.",  # noqa: E501
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = "__all__"
