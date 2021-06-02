import os
from itertools import chain

import django_tables2 as tables
from django.conf import settings
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from . import scheduler
from .filters import JobFilter
from .forms import JobForm, JobTypeForm, ProjectForm, SubmissionForm
from .models import Job, Project
from .software import SOFTWARE
from .tables import JobTable


def index(request):
    admin_email = settings.ADMINS[0][1] if settings.ADMINS else ""
    return render(request, "main/index.html", {"admin_email": admin_email})


def create_job(request, project_pk, resource_index, software_index):
    project = get_object_or_404(Project, pk=project_pk)
    software = SOFTWARE[software_index]
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
            return redirect(
                "main:create_job",
                project.pk,
                form.cleaned_data["resources"],
                form.cleaned_data["software"],
            )
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
