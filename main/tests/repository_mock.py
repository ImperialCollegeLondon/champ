from django.http import HttpResponse

from main.repositories.base_repository import RepositoryBase


class MockRepository(RepositoryBase):
    label = "mock"
    full_name = "A Mock Repository"

    def authorize(self, request):
        return HttpResponse("success")

    def token(self, request):
        return "token"

    def publish(self, request, job, files, metadata):
        self.files = files
        self.metadata = metadata
        return "doi"
