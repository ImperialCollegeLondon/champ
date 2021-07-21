from abc import ABC, abstractmethod


class RepositoryBase(ABC):
    @property
    @abstractmethod
    def label(self):
        """A short label (string) for this repository."""
        pass

    @property
    @abstractmethod
    def full_name(self):
        """A longer descriptive name (string) for this repository"""
        pass

    @abstractmethod
    def publish(self, job, files, metadata):
        """Publish a dataset to the repository.

        Arguments:
        job - a main.models.Job instanceg
        files - a list of dicts of the form -
                [{"name": "name of file", "description": "description of file"}...]
        metadata - a list of dicts of the form -
                [{"name": "name of item", "value": "value of item"}...]
        Return:
        The DOI (string) of the published dataset
        """
        pass

    @abstractmethod
    def request_token(self, request):
        """Perform the required tasks to get an access token from the
        repository provider.

        Arguments:
          request - A Django Request object passed through from a view
        Return:
          A Django response of some kind, usually a redirect
        """
        pass

    @abstractmethod
    def receive_token(self, request):
        """Process a request containing a token from a repository provider.

        Arguments:
          request - A Django Request object passed through from a view
        Return:
          A token (string)
        """
        pass
