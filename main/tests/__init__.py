from ..models import Job, Project


def create_dummy_job(description="desc", project=None):
    if not project:
        project = Project.objects.create(name="project")
    return Job.objects.create_job(description, {}, project, 0, 0)
