from django.shortcuts import redirect, render

from .models import Job


def index(request):
    return render(request, "main/index.html")


def create_job(request):
    if request.method == "POST":
        job = Job.objects.create_job()
        return redirect("main:success", job.pk)
    else:
        return render(request, "main/create_job.html")


def success(request, job_pk):
    job = Job.objects.get(pk=job_pk)
    return render(request, "main/success.html", {"job_id": job.job_id})
