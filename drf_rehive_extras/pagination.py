from collections import OrderedDict

from rest_framework.pagination import (
    PageNumberPagination as RestPageNumberPagination,
    CursorPagination as RestCursorPagination
)
from rest_framework.response import Response


class PageNumberPagination(RestPageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 250

    def get_paginated_response(self, data):
        response = OrderedDict([
            ('count', self.page.paginator.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])

        return Response(
            OrderedDict([('status', 'success'), ('data', response)])
        )


class CursorPagination(RestCursorPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 250
    # TODO, is there a reasonable way we can move orderby_query_param and
    # orderby_fields into the filtersets, views or even models.
    orderby_query_param = "orderby"
    orderby_fields = ("created", "-created",)

    def get_ordering(self, request, queryset, view):
        """
        Return a tuple of strings, that may be used in an `order_by` method.
        """

        # The default case is to check for an `ordering` attribute
        # on this pagination instance.
        ordering = self.ordering

        # Check if the ordering is modified by a query param.
        # Ensure that the ordering in the query param is an allowed field.
        query_param_ordering = request.GET.get(self.orderby_query_param)
        if query_param_ordering in self.orderby_fields:
            ordering = request.GET[self.orderby_query_param]

        assert ordering is not None, (
            'Using cursor pagination, but no ordering attribute was declared '
            'on the pagination class.'
        )
        assert '__' not in ordering, (
            'Cursor pagination does not support double underscore lookups '
            'for orderings. Orderings should be an unchanging, unique or '
            'nearly-unique field on the model, such as "-created" or "pk".'
        )
        assert isinstance(ordering, (str, list, tuple)), (
            'Invalid ordering. Expected string or tuple, but got {type}'.format(
                type=type(ordering).__name__
            )
        )

        if isinstance(ordering, str):
            return (ordering,)

    def get_paginated_response(self, data):
        response = OrderedDict([
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('results', data)
        ])

        return Response(
            OrderedDict([('status', 'success'), ('data', response)])
        )
