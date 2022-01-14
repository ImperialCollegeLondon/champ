import logging

from django.test.runner import DiscoverRunner

from ..models import Job, Project


def create_dummy_job(description="desc", project=None):
    if not project:
        project = Project.objects.create(name="project")
    return Job.objects.create_job(description, {}, project, 0, 0)


class TestSuiteRunner(DiscoverRunner):
    """Custom test runner that disables logging messages"""

    def run_tests(self, *args, **kwargs):
        logging.disable(logging.CRITICAL)
        return super().run_tests(*args, **kwargs)
