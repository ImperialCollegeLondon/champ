from django import forms

from .models import CustomConfig, CustomResource, Job, Profile, Project
from .resources import get_resource_choices
from .software import get_software_choices


class SubmissionForm(forms.Form):
    """Used in the final step before job submission in the create_job view. Form fields
    are generated based on the software configuration provided.
    """

    required_css_class = "required"

    def __init__(self, software, *args, **kwargs):
        """
        args:
          software (dict): The software package on which to base the form. Must follow
            config_validation.SoftwareSchema.
          *args: passed through to base class init method
          **kwargs: passed through to base class init method
        """
        super().__init__(*args, **kwargs)
        self.fields["description"] = forms.CharField(
            max_length=200, label="Description", required=False
        )
        input_files = software["input_files"]
        for spec in input_files["required"]:
            self.fields[spec["key"]] = forms.FileField(label=spec["description"])
        for spec in input_files["optional"]:
            self.fields[spec["key"]] = forms.FileField(
                label=spec["description"], required=False
            )


class JobTypeForm(forms.Form):
    """Used in the initial step of job creation in the job_type view."""

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
        choices=get_software_choices,
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
