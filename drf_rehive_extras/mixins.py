from rest_framework.response import Response
from rest_framework.settings import api_settings
from rest_framework.mixins import (
    CreateModelMixin as DRFCreateModelMixin,
    ListModelMixin as DRFListModelMixin,
    RetrieveModelMixin as DRFRetrieveModelMixin,
    UpdateModelMixin as DRFUpdateModelMixin,
    DestroyModelMixin as DRFDestroyModelMixin
)
from django_filters.rest_framework import DjangoFilterBackend

from .pagination import PageNumberPagination, CursorPagination


def add_resource_data(request, instance):
    """
    Helper function to add resource infomation to the request. This info can
    be used later on in the view context.

    The resource data is populated with the single instance that is created,
    updated or deleted (and does not include other resources modifed as a
    result).

    Resource data will only be populated if a RESOURCE and/or RESOURCE_ID is
    available on the specific model instance.
    """

    # Attempt to a set a resource on the request.
    try:
        resource = getattr(instance, "RESOURCE")
    except AttributeError:
        return
    else:
        request._resource = resource

    # Attempt to a set a resource ID on the request.
    try:
        field = getattr(instance, "RESOURCE_ID")
        resource_id = getattr(instance, field)
    except AttributeError:
        return
    else:
        request._resource_id = str(resource_id)


class ActionMixin(DRFCreateModelMixin):
    """
    Perform a generic action.
    """

    def create(self, request, *args, **kwargs):
        """
        Handle object creation on the view.
        """

        # Handle the request serialization and creation.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Attach creation success headers.
        headers = self.get_success_headers(serializer.data)

        return Response(
            data={'status': 'success'},
            status=self.get_response_status_code(),
            headers=headers
        )


class CreateModelMixin(DRFCreateModelMixin):
    """
    Create a model instance.
    """

    def create(self, request, *args, **kwargs):
        """
        Handle object creation on the view.
        """

        # Handle the request serialization and creation.
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Inject resource data into the request.
        add_resource_data(request, serializer.instance)

        # Attach creation success headers.
        headers = self.get_success_headers(serializer.data)

        # Handle the response serialization. Sometimes the serialization of
        # responses should be different from the request serialization.
        data = self.get_response_serializer(serializer.instance).data

        return Response(
            data={'status': 'success', 'data': data},
            status=self.get_response_status_code(),
            headers=headers
        )


class ListModelMixin(DRFListModelMixin):
    """
    List a queryset.
    """

    filter_backends = (DjangoFilterBackend,)
    pagination_class = PageNumberPagination

    def get_pagination_class(self):
        """
        Get a paginator class based on a pagination field in a GET param.
        """

        paginator_name = self.request.GET.get('pagination')

        try:
            return {
                "page": PageNumberPagination,
                "cursor": CursorPagination
            }[paginator_name]
        except KeyError:
            return self.pagination_class

    @property
    def paginator(self):
        """
        Fetch the correct paginator class.
        """

        if not hasattr(self, '_paginator'):
            pagination_class = self.get_pagination_class()
            if pagination_class is None:
                self._paginator = None
            else:
                self._paginator = pagination_class()

        return self._paginator

    def list(self, request, *args, **kwargs):
        """
        Handle object listing on the view.
        """

        # Get a list of objects as a queryset.
        queryset = self.filter_queryset(self.get_queryset())

        # Paginate the queryset.
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Handle serialization.
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            data={'status': 'success', 'data': serializer.data},
            status=self.get_response_status_code()
        )


class RetrieveModelMixin(DRFRetrieveModelMixin):
    """
    Retrieve a model instance.
    """

    def retrieve(self, request, *args, **kwargs):
        """
        Handle object retrieval on the view.
        """

        # Get a single object.
        instance = self.get_object()

        # Inject resource data into the request.
        add_resource_data(request, instance)

        # Handle serialization.
        serializer = self.get_serializer(instance)

        return Response(
            data={'status': 'success', 'data': serializer.data},
            status=self.get_response_status_code()
        )


class UpdateModelMixin(DRFUpdateModelMixin):
    """
    Update a model instance.
    """

    def update(self, request, *args, **kwargs):
        """
        Handle object update on the view.
        """

        # Find out whether this is a partial (PATCH) or full (PUT) update.
        partial = kwargs.pop('partial', False)

        # Get a single object.
        instance = self.get_object()

        # Inject resource data into the request.
        add_resource_data(request, instance)

        # Handle serialization and update.
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Handle the response serialization. Sometimes the serialization of
        # responses should be different from the request serialization.
        data = self.get_response_serializer(serializer.instance).data

        return Response(
            data={'status': 'success', 'data': data},
            status=self.get_response_status_code(),
        )


class DestroyModelMixin(DRFDestroyModelMixin):
    """
    Destroy a model instance.
    """

    def destroy(self, request, *args, **kwargs):
        """
        Handle object destruction on the view.
        """

        # Get a single object.
        instance = self.get_object()

        # Inject resource data into the request.
        add_resource_data(request, instance)

        # Handle serialization and destroy.
        serializer = self.get_serializer(instance, data=request.data)
        self.perform_destroy(instance)

        return Response(
            data={'status': 'success'},
            status=self.get_response_status_code()
        )

