import csv
import logging
import os
from datetime import timedelta
from itertools import chain

import django_tables2 as tables
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from . import scheduler
from .filters import JobFilter
from .forms import JobForm, JobTypeForm, ProfileForm, ProjectForm, SubmissionForm
from .models import (
    CustomConfig,
    CustomResource,
    Job,
    Profile,
    Project,
    Publication,
    Token,
)
from .repositories import RepositoryError, get_repositories, get_repository
from .software import SOFTWARE
from .tables import (
    CustomConfigTable,
    CustomResourceTable,
    DirectoryTable,
    JobTable,
    PublicationTable,
)
from .utils import file_properties
from .zip_stream import zipfile_generator

logger = logging.getLogger(__name__)


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
                url = reverse("main:list_jobs")
                return redirect(url + f"?success={job.pk}")
            except scheduler.SchedulerError as e:
                logger.exception("Exception during job submission")
                msg = f"Job submission failed\n\n{e.args[0]}"
                return render(request, "main/failed.html", {"message": msg})
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


def list_jobs(request):
    job_filter = JobFilter(request.GET, queryset=Job.objects.order_by("-pk"))
    table = JobTable(job_filter.qs)
    config = tables.RequestConfig(request, paginate={"per_page": 15})
    config.configure(table)

    for job in table.page.object_list.data:
        if job.status != "Completed":
            try:
                job.status = scheduler.status(job.job_id).capitalize()
            except scheduler.SchedulerError:
                # if something goes wrong with getting status info for one
                # job, assume a problem and don't try the rest
                break
            if job.status == "Completed":
                try:
                    with (job.work_dir / "WALLTIME").open() as f:
                        job.walltime = timedelta(seconds=int(f.read()))
                except (IOError, ValueError):
                    pass
            job.save()

    try:
        job = Job.objects.get(pk=int(request.GET["success"]))
        message = f"Successfully submitted job - {job.job_number} ({job.job_id})"
    except (KeyError, Job.DoesNotExist, ValueError):
        message = None
    return render(
        request,
        "main/list_jobs.html",
        {
            "table": table,
            "filter": job_filter,
            "options": (10, 15, 25, 50),
            "message": message,
        },
    )


def delete(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    try:
        job.delete()
    except (scheduler.SchedulerError, OSError):
        logger.exception(f"Error deleting job: Job pk {job.pk}")
        return render(
            request,
            "main/failed.html",
            {
                "message": (
                    "Error encountered whilst deleting job. Please try again later."
                )
            },
        )
    except FileNotFoundError:
        pass
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
    return render(
        request,
        "main/job_type.html",
        {"form": form, "config_link": settings.CONFIG_LINK},
    )


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
    get_object_or_404(Project, pk=project_pk).delete()
    return redirect(request.META.get("HTTP_REFERER", "main:index"))


def job(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect(request.META.get("HTTP_REFERER", "main:index"))
    table = PublicationTable(Publication.objects.filter(job=job))
    return render(request, "main/job.html", {"form": form, "table": table})


def software_help(request, software_index):
    software = SOFTWARE[software_index]
    return render(
        request, "main/software_help.html", {"help_text": software["help_text"]}
    )


def profile(request):
    try:
        profile = Profile.objects.get()
    except Profile.DoesNotExist:
        profile = Profile()
    form = ProfileForm(request.POST or None, instance=profile)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect(request.META.get("HTTP_REFERER", "main:index"))
    configs_table = CustomConfigTable(CustomConfig.objects.all())
    resource_table = CustomResourceTable(CustomResource.objects.all())

    repository_data = []
    for label, repo in get_repositories().items():
        token = Token.objects.filter(label=label).first()
        linked = bool(token)
        repository_data.append(dict(name=repo.full_name, linked=linked, label=label))
    repository_data.sort(key=lambda x: x["name"])
    return render(
        request,
        "main/profile.html",
        {
            "form": form,
            "configs_table": configs_table,
            "resource_table": resource_table,
            "repository_data": repository_data,
        },
    )


def delete_profile(request):
    try:
        profile = Profile.objects.get()
        profile.delete()
    except Profile.DoesNotExist:
        pass
    return redirect(request.META.get("HTTP_REFERER", "main:index"))


def custom_config(request, pk=None, form_class=None):
    model = form_class.Meta.model
    if pk is None:
        instance = model()
    else:
        instance = get_object_or_404(model, pk=pk)
    form = form_class(request.POST or None, instance=instance)
    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("main:profile")
    return render(
        request, "main/custom_config.html", {"form": form, "create": pk is None}
    )


def custom_config_delete(request, pk, klass):
    instance = get_object_or_404(klass, pk=pk)
    instance.delete()
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


def publish(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    try:
        profile = Profile.objects.get()
        profile.full_clean()
    except (Profile.DoesNotExist, ValidationError):
        profile_url = reverse("main:profile")
        return render(
            request,
            "main/failed.html",
            {
                "message": (
                    "Profile information not set. Please complete your "
                    f'<a href="{profile_url}">profile</a> to publish.'
                )
            },
        )

    if job.published:
        return render(
            request,
            "main/failed.html",
            {"message": "Job already published"},
        )

    if not Token.objects.count():
        profile_url = reverse("main:profile")
        return render(
            request,
            "main/failed.html",
            {
                "message": (
                    "No linked data repositories found. Please link with a repository "
                    f'via <a href="{profile_url}">Profile</a>'
                )
            },
        )

    if not job.description:
        return render(
            request,
            "main/failed.html",
            {"message": "Job must have a description to be published"},
        )
    try:
        with open(job.work_dir / "FILES_TO_PUBLISH") as f:
            files = list(csv.DictReader(f, delimiter="\t"))
    except IOError:
        return render(
            request,
            "main/failed.html",
            {
                "message": (
                    "Unable to open 'FILES_TO_PUBLISH' in job directory. This usually "
                    "means the job did not complete within its allotted walltime."
                )
            },
        )
    try:
        with open(job.work_dir / "METADATA") as f:
            metadata = list(csv.DictReader(f, delimiter="\t"))
    except IOError:
        return render(
            request,
            "main/failed.html",
            {"message": "Unable to open 'METADATA' in job directory"},
        )

    try:
        for repo in get_repositories().values():
            if Token.objects.filter(label=repo.label).last():
                doi = repo.publish(request, job, files, metadata)
                Publication.objects.create(
                    job=job, repo_label=repo.label, repo_name=repo.full_name, doi=doi
                )
    except RepositoryError:
        logger.exception(f"Exception whilst publishing to {repo.full_name}")
        return render(
            request,
            "main/failed.html",
            {"message": f"Error publishing to {repo.full_name}"},
        )

    return redirect("main:job", job.pk)


def authorize(request, repo_label):
    repository = get_repository(repo_label)
    return repository.authorize(request)


def token(request, repo_label):
    repo = get_repository(repo_label)
    try:
        repo.token(request)
    except RepositoryError:
        logging.exception(
            f"Error from repository in response to linking request: {repo.full_name}."
        )
        return render(
            request,
            "main/failed.html",
            {"message": "Linking failed."},
        )

    return redirect("main:profile")


def delete_token(request, repo_label):
    token = get_object_or_404(Token, label=repo_label)
    token.delete()
    return redirect(request.META.get("HTTP_REFERER", "main:index"))


def directory(request, job_pk):
    job = get_object_or_404(Job, pk=job_pk)
    if not job.work_dir.exists():

        return render(
            request,
            "main/failed.html",
            {"message": "Job directory not found. It may have been deleted."},
        )

    files = [file_properties(path) for path in job.work_dir.glob("*")]
    files.sort(key=lambda x: x["name"])
    table = DirectoryTable(files)
    config = tables.RequestConfig(request)
    config.configure(table)
    directory_url = os.getenv("OOD_FILES_URL", "") + "/fs" + str(job.work_dir)
    return render(
        request,
        "main/directory.html",
        {"table": table, "directory_url": directory_url, "job": job},
    )
