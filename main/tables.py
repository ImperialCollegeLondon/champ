import django_tables2 as tables

from .models import CustomConfig, Job


class JobTable(tables.Table):
    class Meta:
        model = Job
        template_name = "django_tables2/semantic.html"
        fields = (
            "pk",
            "software",
            "description",
            "resources",
            "status",
            "submission_time",
            "project",
        )

    work_dir = tables.TemplateColumn(
        "<a href={{ base_url }}/{{ value }}>Open directory</a>",
        orderable=False,
        verbose_name="",
    )
    pk = tables.Column(linkify=True, verbose_name="Job Number")

    def render_pk(self, value):
        return f"{value:08d}"


class CustomConfigTable(tables.Table):
    class Meta:
        model = CustomConfig
        template_name = "django_tables2/semantic.html"
        fields = ("label", "pk")

    pk = tables.TemplateColumn(
        "<a href=\"{% url 'main:custom_config' value %}\"/>Edit</a><br>"
        "<a href=\"{% url 'main:custom_config_delete' value %}\"/>Delete</a><br>",
        orderable=False,
        verbose_name="",
    )
