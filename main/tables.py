import django_tables2 as tables
from django.urls import reverse
from django.utils.html import format_html

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
    publish = tables.Column(verbose_name="", empty_values=())
    delete_ = tables.TemplateColumn(
        "<a href=\"{% url 'main:delete' record.pk %}\">Delete</a>", verbose_name=""
    )
    walltime = tables.Column(verbose_name="Runtime")
    pk = tables.Column(linkify=True, verbose_name="Job Number")

    def render_pk(self, value):
        return f"{value:08d}"

    def render_publish(self, record):
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


class PublicationTable(tables.Table):
    class Meta:
        model = Publication
        template_name = "django_tables2/semantic.html"
        fields = ("repo_name", "doi")

    repo_name = tables.Column(verbose_name="Repository")
    doi = tables.Column(linkify=lambda record: record.link, verbose_name="DOI")


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
