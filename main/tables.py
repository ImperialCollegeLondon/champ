import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

from .models import CustomConfig, CustomResource, Job, Publication


class JobTable(tables.Table):
    class Meta:
        model = Job
        template_name = "main/job_table.html"
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
    publish = tables.Column(verbose_name="Repository", empty_values=(), orderable=False)
    delete_ = tables.TemplateColumn(
        "<a href=\"{% url 'main:delete' record.pk %}\" onclick=\"return confirm('You are about to delete job {{record.job_number}}. Are you sure?')\">Delete</a>",  # noqa: E501
        verbose_name="",
    )
    walltime = tables.Column(verbose_name="Runtime")
    pk = tables.Column(linkify=True, verbose_name="Job Number")

    def render_pk(self, value):
        return f"{value:08d}"

    def render_publish(self, record):
        if record.status != "Completed":
            return ""
        publications = Publication.objects.filter(job=record)
        if publications:
            return format_html(
                "<br>".join(
                    f'<a href="{pub.link}">{pub.doi}</a>' for pub in publications
                )
            )
        else:
            url = reverse("main:publish", args=[record.pk])
            return format_html(f'<a href="{url}">Publish</a>')


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


class CustomResourceTable(CustomConfigTable):
    class Meta:
        model = CustomResource
        template_name = "django_tables2/semantic.html"
        fields = ("label", "pk")

    pk = tables.TemplateColumn(
        "<a href=\"{% url 'main:custom_resource' value %}\"/>Edit</a><br>"
        "<a href=\"{% url 'main:custom_resource_delete' value %}\"/>Delete</a><br>",
        orderable=False,
        verbose_name="",
    )


class PublicationTable(tables.Table):
    class Meta:
        model = Publication
        template_name = "django_tables2/semantic.html"
        fields = ("repo_name", "doi")

    repo_name = tables.Column(verbose_name="Repository")
    doi = tables.Column(linkify=lambda record: record.link, verbose_name="DOI")
    metadata = tables.TemplateColumn(
        '<a href="https://data.datacite.org/application/vnd.datacite.datacite+xml/{{ record.doi }}">Metadata</a>',  # noqa: 501
        verbose_name="Publication Metadata",
    )


class DirectoryTable(tables.Table):
    class Meta:
        template_name = "django_tables2/semantic.html"

    name = tables.Column(verbose_name="File Name")
    mtime = tables.Column(verbose_name="Last Modified")
    file_size = tables.Column(verbose_name="Size")
    view = tables.TemplateColumn(
        '<a href="{{ directory_url }}/{{ record.name }}" target="_blank" class="external-link">View</a>',  # noqa: E501
        verbose_name="",
    )
    download = tables.TemplateColumn(
        '<a href="{{ directory_url }}/{{ record.name }}?download=1">Download</a>',
        verbose_name="",
    )
