from django.utils.translation import gettext_lazy as _
from rest_framework import status
from rest_framework.generics import GenericAPIView

from . import mixins


class BaseAPIView(GenericAPIView):
    """
    Generic view with extended features. All viewsets should extend this class.
    """

    # Modify the serializer classes used by the view based on the request
    # method.
    # This attribute can take two formats:
    #  - {"GET": ObjectSerializer}
    #  - {"GET": (RequestObjectSerializer, ResponseObjectSerializer,)}
    serializer_classes = {}

    # Modify the statuses used by the view based on the request method.
    # This attributes can take the following format:
    #  - `{"GET": status.HTTP_200_OK}`
    response_status_codes = {}

    # The default statuses used by the view based on the request method.
    default_response_status_codes = {
        "GET": status.HTTP_200_OK,
        "POST": status.HTTP_201_CREATED,
        "PUT": status.HTTP_200_OK,
        "PATCH": status.HTTP_200_OK,
        # NOTE : We use 200 for deletes instead of 204 because the Rehive
        # response format supports a `status` in the body and by default
        # 204 expects there to be no response body.
        "DELETE": status.HTTP_200_OK,
    }

    def get_serializer_class(self):
        """
        Retrieve the request serializer class for the view.

        If the item returned from the serializer_classes is a tuple or list then
        get the first class.
        """

        try:
            c = self.serializer_classes[self.request.method]
        except KeyError:
            return super().get_serializer_class()

        if isinstance(c, (tuple, list)) and len(c) >= 1:
            return c[0]
        else:
            return c

    def get_response_serializer_class(self):
        """
        Retrieve the response serializer class for the view.

        If the item returned from the serializer_classes is a tuple or list then
        get the second class if possible, otherwise get the first class.
        """

        try:
            c = self.serializer_classes[self.request.method]
        except KeyError:
            return super().get_serializer_class()

        if isinstance(c, (tuple, list)) and len(c) >= 1:
            try:
                return c[1]
            except KeyError:
                return c[0]
        else:
            return c

    def get_response_serializer(self, *args, **kwargs):
        """
        Get the response serializer. Uses the custom
        `get_response_serializer_class` instead of the default
        `get_serializer_class`.
        """

        serializer_class = self.get_response_serializer_class()
        kwargs.setdefault('context', self.get_serializer_context())
        return serializer_class(*args, **kwargs)

    def get_response_status_code(self):
        """
        Get the response status code.
        """

        try:
            return self.response_status_codes[self.request.method]
        except KeyError:
            return self.default_response_status_codes[self.request.method]


class ActionAPIView(mixins.ActionMixin,
                    BaseAPIView):
    """
    Concrete view for performing a generic action.
    """

    response_status_codes = {
        "POST": status.HTTP_200_OK
    }

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class CreateAPIView(mixins.CreateModelMixin,
                    BaseAPIView):
    """
    Concrete view for creating a model instance.
    """

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class ListAPIView(mixins.ListModelMixin,
                  BaseAPIView):
    """
    Concrete view for listing a queryset.
    """

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class RetrieveAPIView(mixins.RetrieveModelMixin,
                      BaseAPIView):
    """
    Concrete view for retrieving a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class DestroyAPIView(mixins.DestroyModelMixin,
                     BaseAPIView):
    """
    Concrete view for deleting a model instance.
    """

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class UpdateAPIView(mixins.UpdateModelMixin,
                    BaseAPIView):
    """
    Concrete view for updating a model instance.
    """
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class ListCreateAPIView(mixins.ListModelMixin,
                        mixins.CreateModelMixin,
                        BaseAPIView):
    """
    Concrete view for listing a queryset or creating a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class RetrieveUpdateAPIView(mixins.RetrieveModelMixin,
                            mixins.UpdateModelMixin,
                            BaseAPIView):
    """
    Concrete view for retrieving and updating a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class RetrieveDestroyAPIView(mixins.RetrieveModelMixin,
                             mixins.DestroyModelMixin,
                             BaseAPIView):
    """
    Concrete view for retrieving and deleting a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class RetrieveUpdateDestroyAPIView(mixins.RetrieveModelMixin,
                                   mixins.UpdateModelMixin,
                                   mixins.DestroyModelMixin,
                                   BaseAPIView):
    """
    Concrete view for retrieving, updating and deleting a model instance.
    """

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
