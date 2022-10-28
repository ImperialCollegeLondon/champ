from django.urls import path

from . import views
from .forms import CustomConfigForm, CustomResourceForm
from .models import CustomConfig, CustomResource

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path(
        "create_job/<int:project_pk>/<int:resource_index>/<int:software_index>/",
        views.create_job,
        name="create_job",
    ),
    path(
        "create_job/<int:project_pk>/<int:resource_index>/<int:software_index>/<int:config_pk>/",  # noqa: E501
        views.create_job,
        name="create_job",
    ),
    path("list_jobs/", views.list_jobs, name="list_jobs"),
    path("delete/<int:job_pk>/", views.delete, name="delete"),
    path("job_type/", views.job_type, name="job_type"),
    path("projects/", views.projects, name="projects"),
    path(
        "delete_project/<int:project_pk>/", views.delete_project, name="delete_project"
    ),
    path("job/<int:job_pk>/", views.job, name="job"),
    path(
        "software_help/<int:software_index>/", views.software_help, name="software_help"
    ),
    path("profile/", views.profile, name="profile"),
    path("delete_profile/", views.delete_profile, name="delete_profile"),
    path(
        "custom_config/",
        views.custom_config,
        {"form_class": CustomConfigForm},
        name="custom_config",
    ),
    path(
        "custom_config/<int:pk>/",
        views.custom_config,
        {"form_class": CustomConfigForm},
        name="custom_config",
    ),
    path(
        "custom_config/delete/<int:pk>/",
        views.custom_config_delete,
        {"klass": CustomConfig},
        name="custom_config_delete",
    ),
    path(
        "custom_config/resource/",
        views.custom_config,
        {"form_class": CustomResourceForm},
        name="custom_resource",
    ),
    path(
        "custom_config/resource/<int:pk>/",
        views.custom_config,
        {"form_class": CustomResourceForm},
        name="custom_resource",
    ),
    path(
        "custom_config/resource/delete/<int:pk>/",
        views.custom_config_delete,
        {"klass": CustomResource},
        name="custom_resource_delete",
    ),
    path("download/<int:job_pk>/", views.download, name="download"),
    path("authorize/<str:repo_label>/", views.authorize, name="authorize"),
    path("token/<str:repo_label>/", views.token, name="token"),
    path("publish/<int:job_pk>/", views.publish, name="publish"),
    path("delete_token/<str:repo_label>/", views.delete_token, name="delete_token"),
    path("directory/<int:job_pk>/", views.directory, name="directory"),
]
