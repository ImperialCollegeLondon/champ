import django_filters

from .models import Job


class JobFilter(django_filters.FilterSet):
    """Filter for Job objects used by the list_jobs view"""

    class Meta:
        model = Job
        fields = ("description", "project", "status", "resources", "software")

    description = django_filters.CharFilter(lookup_expr="icontains")
    not_description = django_filters.CharFilter(
        field_name="description",
        lookup_expr="icontains",
        exclude=True,
        label="Description does not contain",
    )
    status = django_filters.ChoiceFilter(
        choices=(
            ("Completed", "Completed"),
            ("Queueing", "Queueing"),
            ("Running", "Running"),
        )
    )
    resources = django_filters.AllValuesFilter()
    software = django_filters.AllValuesFilter()
