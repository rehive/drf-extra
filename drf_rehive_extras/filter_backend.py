from collections import OrderedDict

from django_filters import rest_framework as filters


class RehiveRestFilterBackend(filters.DjangoFilterBackend):
    def get_ordering(self, request, queryset, view):
        """
        This method is to support ordering in `CursorPagination`.

        States:
            * default_ordering: This is used for configure the default ordering.
              By default it is `-created`.
            * ordering_lookup_fields: This is used for limiting the order fields.
            By default it is `(created,)`.
            * orderby_key: This is used for configuring the `query param key`
            for the ordering. By default it is `orderby`.

            Note: Above values can be configured from the views.

            * get_ordering_value: This method is used for controlling the
              behaviour. This method can be implemented in the `FilterSet`.
        """

        default_ordering = getattr(view, 'ordering_fields', '-created')
        ordering_lookup_fields = tuple(getattr(
            view, 'ordering_lookup_fields', ('created',)))
        orderby_key = getattr(view, 'orderby_key', 'orderby')
        # Get the orderby value from query parameter.
        orderby_value = self.get_filterset_kwargs(
            request, queryset, view)['data'].get(orderby_key, None)
        filter_class = self.get_filterset_class(view, queryset)

        if not orderby_value or not filter_class \
                or not hasattr(filter_class, 'get_ordering_value'):
            return default_ordering

        # Get the ordering from `FilterSet` class.
        ordering = filter_class(
            OrderedDict(orderby_key=orderby_value)
        ).get_ordering_value(orderby_value)

        # Check the ordering are present in the ordering_lookup_fields
        # otherwise return the default_ordering.
        return ordering if ordering[0].lstrip('-') in ordering_lookup_fields \
            else default_ordering
