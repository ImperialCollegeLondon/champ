import django_tables2 as tables

from .models import CustomConfig, Job, Publication


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
            "walltime",
            "submission_time",
            "project",
        )
        attrs = {"class": "ui compact celled table"}

    work_dir = tables.TemplateColumn(
        "<a href=\"{% url 'main:directory' record.pk %}\">"
        'Open</a>{% if record.status == "Completed"%}<br>'
        '<a href="{% url \'main:download\' record.pk %}" class="blocking">Download</a>'
        "{% endif %}",
        orderable=False,
        verbose_name="Directory",
    )
    publish = tables.TemplateColumn(
        "{% if record.status == 'Completed' and not record.published %}"
        '<a href="{% url \'main:publish\' record.pk %}" class="blocking">Publish</a>'
        "{% endif %}",
        verbose_name="",
    )
    delete_ = tables.TemplateColumn(
        "<a href=\"{% url 'main:delete' record.pk %}\">Delete</a>", verbose_name=""
    )
    walltime = tables.Column(verbose_name="Runtime")
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


class PublicationTable(tables.Table):
    class Meta:
        model = Publication
        template_name = "django_tables2/semantic.html"
        fields = ("repo_name", "doi")

    repo_name = tables.Column(verbose_name="Repository")
    doi = tables.Column(linkify=lambda record: record.link)


class DirectoryTable(tables.Table):
    class Meta:
        template_name = "django_tables2/semantic.html"

    name = tables.Column(verbose_name="File Name")
    mtime = tables.Column(verbose_name="Last Modified")
    file_size = tables.Column(verbose_name="Size")
    view = tables.TemplateColumn(
        '<a href="{{ directory_url }}/{{ record.name }}">View</a>',
        verbose_name="",
    )
