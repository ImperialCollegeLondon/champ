from ..models import Job


def create_dummy_job(project):
    return Job.objects.create_job("", {}, project, 0)
