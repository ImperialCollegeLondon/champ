import os
from itertools import chain

import django_tables2 as tables
from django.conf import settings
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from . import scheduler
from .filters import JobFilter
from .forms import CustomConfigForm, JobForm, JobTypeForm, ProjectForm, SubmissionForm
from .models import CustomConfig, Job, Project
from .software import SOFTWARE
from .tables import CustomConfigTable, JobTable
from .zip_stream import zipfile_generator


def index(request):
    admin_email = settings.ADMINS[0][1] if settings.ADMINS else ""
    return render(request, "main/index.html", {"admin_email": admin_email})


def create_job(request, project_pk, resource_index, software_index, config_pk=None):
    project = get_object_or_404(Project, pk=project_pk)
    software = SOFTWARE[software_index]
    custom_config = (
        None if config_pk is None else get_object_or_404(CustomConfig, pk=config_pk)
    )
    if request.method == "POST":
        form = SubmissionForm(software, request.POST, request.FILES)
        files_spec = software["input_files"]
        if form.is_valid():
            input_files = {
                key: request.FILES[key]
                for key in chain(files_spec["required"], files_spec["optional"])
                if key in request.FILES
            }
            try:
                job = Job.objects.create_job(
                    form.cleaned_data["description"],
                    input_files,
                    project,
                    resource_index,
                    software_index,
                    custom_config,
                )
                return redirect("main:success", job.pk)
            except scheduler.SchedulerError:
                return redirect("main:failed")
    else:
        form = SubmissionForm(software)
    return render(
        request,
        "main/create_job.html",
        {
            "form": form,
            "software_help_url": reverse(
                "main:software_help", kwargs={"software_index": software_index}
            ),
        },
    )


def success(request, job_pk):
    job = Job.objects.get(pk=job_pk)
    return render(request, "main/success.html", {"job_id": job.job_id})


def failed(request):
    return render(request, "main/failed.html")


def list_jobs(request):
    job_filter = JobFilter(request.GET, queryset=Job.objects.order_by("-pk"))
    table = JobTable(job_filter.qs)
    config = tables.RequestConfig(request, paginate={"per_page": 10})
    config.configure(table)

    for job in table.page.object_list.data:
        if job.status != "Completed":
            try:
                job.status = scheduler.status(job.job_id).capitalize()
            except scheduler.SchedulerError:
                # if something goes wrong with getting status info for one
                # job, assume a problem and don't try the rest
                break
            job.save()

    return render(
        request,
        "main/list_jobs.html",
        {
            "table": table,
            "base_url": os.getenv("OOD_FILES_URL", "") + "/fs",
            "filter": job_filter,
            "options": (10, 25, 50),
        },
    )


def delete(request, job_pk):
    job = Job.objects.get(pk=job_pk)
    job.delete()
    return redirect(request.META.get("HTTP_REFERER", "main:index"))


def job_type(request):
    if request.method == "POST":
        form = JobTypeForm(request.POST)
        if form.is_valid():
            project = form.cleaned_data["project"]
            args = [form.cleaned_data["resources"], form.cleaned_data["software"]]
            custom_config = form.cleaned_data["custom_config"]
            if custom_config:
                args.append(custom_config.pk)
            return redirect("main:create_job", project.pk, *args)
    else:
        form = JobTypeForm()
    return render(request, "main/job_type.html", {"form": form})


def projects(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(request.META.get("HTTP_REFERER", "main:index"))
    else:
        form = ProjectForm()
    projects = Project.objects.all()
    return render(request, "main/projects.html", {"projects": projects, "form": form})


def delete_project(request, project_pk):
    Project.objects.get(pk=project_pk).delete()
    return redirect(request.META.get("HTTP_REFERER", "main:index"))


def job(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect(request.META.get("HTTP_REFERER", "main:index"))
    return render(request, "main/job.html", {"form": form})


def software_help(request, software_index):
    software = SOFTWARE[software_index]
    return render(
        request, "main/software_help.html", {"help_text": software["help_text"]}
    )


def profile(request):
    table = CustomConfigTable(CustomConfig.objects.all())
    return render(
        request,
        "main/profile.html",
        {"table": table},
    )


def custom_config(request, config_pk=None):
    if config_pk is None:
        config = CustomConfig()
    else:
        config = get_object_or_404(CustomConfig, pk=config_pk)
    if request.method == "POST":
        form = CustomConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            return redirect("main:profile")
    else:
        form = CustomConfigForm(instance=config)
    return render(
        request, "main/custom_config.html", {"form": form, "create": config_pk is None}
    )


def custom_config_delete(request, config_pk):
    config = CustomConfig.objects.get(pk=config_pk)
    config.delete()
    return redirect(request.META.get("HTTP_REFERER", "main:index"))


def download(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    if job.status != "Completed":
        raise Http404("Job not completed")
    dir_name = job.work_dir.name
    return StreamingHttpResponse(
        zipfile_generator(dir_name, job.work_dir.glob("*")),
        content_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{dir_name}.zip"'},
    )
