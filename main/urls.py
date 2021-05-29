from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "create_job/<int:project_pk>/<int:resource_index>/",
        views.create_job,
        name="create_job",
    ),
    path("success/<int:job_pk>/", views.success, name="success"),
    path("failed/", views.failed, name="failed"),
    path("list_jobs/", views.list_jobs, name="list_jobs"),
    path("delete/<int:job_pk>/", views.delete, name="delete"),
    path("job_type/", views.job_type, name="job_type"),
    path("projects/", views.projects, name="projects"),
    path(
        "delete_project/<int:project_pk>/", views.delete_project, name="delete_project"
    ),
    path("job/<int:job_pk>/", views.job, name="job"),
]
