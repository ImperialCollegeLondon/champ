import django_tables2 as tables

from .models import Job


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
