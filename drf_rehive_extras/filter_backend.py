from collections import OrderedDict

from django_filters import rest_framework as filters


class RehiveRestFilterBackend(filters.DjangoFilterBackend):
    def get_ordering(self, request, queryset, view):
        default_ordering = getattr(view, 'ordering_fields', '-created')
        orderby_key = getattr(view, 'orderby_key', 'orderby')
        orderby_value = self.get_filterset_kwargs(
            request, queryset, view)['data'].get(orderby_key, None)
        filter_class = self.get_filterset_class(view, queryset)

        if not orderby_value or not filter_class \
                or not hasattr(filter_class, 'get_ordering_value'):
            return default_ordering

        ordering = filter_class(
            OrderedDict(orderby_key=orderby_value)
        ).get_ordering_value(orderby_value)

        return ordering if ordering[0].lstrip('-') in ['created', 'updated'] \
            else default_ordering
