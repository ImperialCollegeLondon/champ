import os

from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from requests_oauthlib import OAuth2Session

from main.models import Profile, Token
from main.repositories import RepositoryError, register
from main.repositories.base_repository import RepositoryBase

ZENODO_CLIENT_ID = os.getenv("ZENODO_CLIENT_ID", "")
ZENODO_CLIENT_SECRET = os.getenv("ZENODO_CLIENT_SECRET", "")


@register
class ZenodoRepository(RepositoryBase):
    label = "zenodo"
    full_name = "Zenodo"
    base_url = "https://zenodo.org/"
    api_url = base_url + "api/"
    token_url = base_url + "oauth/token"

    def get_oauth_session(self, request, state=None):
        """Return a requests_oauthlib.OAuth2Session object suitable for token
        acquisition or interaction with the Zenodo API. If a token
        exists for this repository in the database its data is used to
        initialise the session and authenticated requests will be
        enabled. The `state` argument is passed through to the session
        object if provided.
        """

        try:
            token_obj = Token.objects.get(label=self.label)
            token_dict = {
                "access_token": token_obj.value,
                "refresh_token": token_obj.refresh_token,
                "token_type": "Bearer",
                "expires_in": (token_obj.expires - timezone.now()).total_seconds(),
            }
        except Token.DoesNotExist:
            token_dict = None
        redirect_uri = request.build_absolute_uri(
            reverse("main:token", args=[self.label])
        )
        return OAuth2Session(
            ZENODO_CLIENT_ID,
            redirect_uri=redirect_uri,
            scope=["deposit:actions", "deposit:write"],
            state=state,
            token=token_dict,
            auto_refresh_url=self.token_url,
            auto_refresh_kwargs={
                "client_id": ZENODO_CLIENT_ID,
                "client_secret": ZENODO_CLIENT_SECRET,
            },
            token_updater=self.save_token,
        )

    def authorize(self, request):
        """Perform the required tasks to get an access token from the
        repository provider.

        Arguments:
          request - A Django Request object passed through from a view
        Return:
          A Django response of some kind, usually a redirect
        """
        oauth = self.get_oauth_session(request)
        authorization_url, state = oauth.authorization_url(
            self.base_url + "oauth/authorize"
        )
        request.session["oauth_state"] = state
        return redirect(authorization_url)

    def save_token(self, token_dict):
        """Callback function used by OAuth2Session to store a new or refreshed
        token in the database.
        """
        Token.objects.update_or_create(
            label=self.label,
            defaults=dict(
                value=token_dict["access_token"],
                refresh_token=token_dict["refresh_token"],
                expires=timezone.datetime.fromtimestamp(token_dict["expires_at"]),
            ),
        )

    def token(self, request):
        """Process a request containing a token from a repository
        provider. This function should create or update an existing
        models.Token object.

        Arguments:
          request - A Django Request object passed through from a view
        Return:
          None
        """
        if "error" in request.GET:
            raise RepositoryError("Invalid response received from repository")

        try:
            session = self.get_oauth_session(
                request, state=request.session.pop("oauth_state")
            )
        except KeyError:
            raise RepositoryError("Invalid response received from repository")

        token = session.fetch_token(
            self.token_url,
            code=request.GET["code"],
            include_client_id=True,
            client_secret=ZENODO_CLIENT_SECRET,
            client_id=ZENODO_CLIENT_ID,
        )

        self.save_token(token)

    def publish(self, request, job, files, metadata):
        """Publish a dataset to the repository.

        Arguments:
        request - a django.HttpRequest object
        job - a main.models.Job instance
        files - a list of dicts of the form -
                [{"name": "name of file", "description": "description of file"}...]
        metadata - a list of dicts of the form -
                [{"name": "name of item", "value": "value of item"}...]
        Return:
        The DOI (string) of the published dataset
        """
        session = self.get_oauth_session(request)
        deposition = self.create_deposition(session)
        self.set_metadata(session, deposition["links"]["self"], job, metadata)

        bucket_url = deposition["links"]["bucket"]
        for file_info in files:
            self.upload_file(
                session,
                bucket_url,
                job.work_dir,
                file_info["name"],
                file_info["description"],
            )
        self.make_public(session, deposition["links"]["publish"])
        return deposition["metadata"]["prereserve_doi"]["doi"]

    def make_public(self, session, publish_url):
        """Publish a deposition via the Zenodo API. Note that this makes the
        DOI live and the deposition can no longer be deleted.
        """
        self.api_request(publish_url, method=session.post)

    def create_deposition(self, session):
        """Create a new deposition via the Zenodo API."""
        return self.api_request(
            self.api_url + "deposit/depositions", method=session.post, json={}
        )

    def set_metadata(self, session, deposition_url, job, metadata):
        """Set the metadata for a deposition via the Zenodo API."""
        profile = Profile.objects.get()
        metadata = {
            "metadata": dict(
                upload_type="dataset",
                title=job.description,
                description=job.software + " calculation",
                access_right="open",
                creators=[
                    dict(
                        name=profile.family_name + ", " + profile.given_names,
                        affiliation=profile.affiliation,
                        orcid=profile.orcid_id,
                    ),
                ],
                keywords=[item["value"] for item in metadata],
            )
        }
        self.api_request(deposition_url, method=session.put, json=metadata)

    def upload_file(self, session, bucket_url, job_dir, name, description):
        """Upload an individual file to a deposition via the Zenodo API."""
        url = f"{bucket_url}/{name}"
        with open(job_dir / name, "rb") as f:
            self.api_request(url, data=f, method=session.put)

    def api_request(self, url, method, data=None, json=None):
        """Helper function for making calls to the Zenodo API. Returns the
        decoded JSON response from the API."""
        response = method(url, data=data, json=json)
        response.raise_for_status()
        return response.json()
