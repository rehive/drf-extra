import os
import yaml
from logging import getLogger
from functools import lru_cache

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import (
    is_list_serializer, is_serializer, is_basic_type, force_instance,
    build_basic_type, is_list_serializer_customized, build_array_type,
    ResolvedComponent, build_media_type_object,
    modify_media_types_for_versioning
)
from drf_spectacular.drainage import get_override
from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import OpenApiResponse
from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.types import OpenApiTypes

from .generics import BaseAPIView
from .serializers import ActionResponseSerializer


logger = getLogger('django')


# Custom documentation handlers.

class Documentation:
    """
    Documentation object that can be used to access YAML that contains extra
    documentation for views.

    The YAML docs should be Formatted as:

        app.views.ExampleView:
            GET:
                operationId:
                summary:
                description:
                x-code-samples:
                    - lang:
                      label:
                      source: >
                    - lang: Python
                      label: Python SDK
                      source: >

    Additional fields used by redoc/swagger can also be added.
    """

    # Store the docs for a given instantiation of the class.
    docs = None

    def __init__(self, dirs=None):
        """
        Initiate the docs class with a path to a YAML file.

        Allows for `dirs` to be customized but will default to
        `settings.ADDITIONAL_DOCS_DIRS` if no dirs are included.
        """

        if not dirs:
            dirs = getattr(settings, 'ADDITIONAL_DOCS_DIRS', [])

        paths = self.get_paths(dirs)
        self.docs = self.collect_docs(paths)

    def get_paths(self, dirs):
        """
        Get a list of file paths to *.yaml files in the documentation dirs.
        """

        paths = []
        for d in dirs:
            try:
                for f in os.listdir(d):
                    if f.endswith(".yaml"):
                        paths.append("{}{}".format(d, f))
            except FileNotFoundError:
                logger.info("Directory not found {}.".format(d))

        return paths

    def collect_docs(self, paths):
        """
        Collect docs in the project and combine into a single dictionary.
        """

        all_docs = None
        for path in paths:
            with open(path, 'r') as file:
                try:
                    docs = yaml.safe_load(file)
                except yaml.YAMLError as exc:
                    logger.info(exc)
                else:
                    # If all docs has not bee populated yet, set it as a dict
                    # first so we can run updates on it.
                    if not all_docs:
                        all_docs = {}
                    all_docs.update(docs)

        return all_docs


@lru_cache(maxsize=None)
def get_additional_documentation():
    """
    Method to get additional documentation.

    Cache the result so it does not have to call it repeatedly.
    """

    return Documentation()


# Extensions

class OneOfOpenApiSerializerExtensionMixin():
    """
    Mixin for SerializerExtensions that must offer a oneOf interface.
    """

    oneof_serializers = []

    def map_serializer(self, auto_schema, direction):
        schema = {"oneOf": []}

        for serializer in self.oneof_serializers:
            sub_schema = auto_schema.resolve_serializer(
                serializer, direction,
            ).ref
            schema["oneOf"].append(sub_schema)

        return schema


# Autoschema

class BaseAutoSchema(AutoSchema):
    """
    Custom extension of the drf-spectacular.AutoSchema to support automated
    documentation injection into the schema.

    Additionally updated the Swagger schema generation to:
        - Envelope the response in a `data` attribute.
    """

    def _log_warning(self, msg):
        """
        Helper to log warnings when DEBUG is True.
        """

        if not settings.DEBUG:
            return

        logger.warning(msg)

    def _get_view_docs(self):
        """
        Helper to get additional docs for a view.

        A `Documentation` instance must be found in settings.ADDITIONAL_DOCS.
        """

        try:
            docs = get_additional_documentation().docs
        except (NameError, AttributeError):
            return None

        # Create a key for the specific view and check if it exists.
        key = "{}.{}".format(self.view.__module__, self.view.__class__.__name__)
        try:
            return docs[key][self.method]
        except (KeyError, TypeError):
            self._log_warning(
                "No additional documentation is defined for the {}"
                " view and {} method.".format(key, self.method)
            )
            return None

    def _get_attr_from_view_docs(self, attribute):
        """
        Helper to get a specific attribute in the views additional docs.
        """

        view_docs = self._get_view_docs()

        if not view_docs:
            return None

        return view_docs.get(attribute, None)

    def _get_envelope(
                self,
                schema,
                serializer,
                direction='response',
                serializer_name=None
            ):
        """
        Get an envelope for the schema if the view or serializer require it.
        """

        # Only BaseAPIView(s) require an envelope.
        if not isinstance(self.view, BaseAPIView):
            return None

        # ActionResponseSerializer(s) do not require an envelope.
        if isinstance(serializer, ActionResponseSerializer):
            return None

        # Base envelope schema.
        envelope_schema = {
            'type': 'object',
            'properties': {
                'status': {
                    'type': 'string',
                    'example': 'success',
                },
                'data': schema
            },
        }

        # Generate a serializer name if one is not manually set.
        if not serializer_name:
            serializer_name = self._get_serializer_name(serializer, direction)

        # Generate and register an envelope component.
        envelope = ResolvedComponent(
            name='{}Response'.format(serializer_name),
            type=ResolvedComponent.SCHEMA,
            schema=envelope_schema,
            object=serializer,
        )
        self.registry.register_on_missing(envelope)

        return envelope

    def _get_response_for_code(
                self,
                serializer,
                status_code,
                media_types=None,
                direction='response'
            ):
        """
        Override the method to attach envelopes to all responses including the
        paginated responses.

        NOTE : This method is almost completely copied directly from:
            https://github.com/tfranzel/drf-spectacular/blob/e0f749e9857d938693311af67bd575800cbc6aab/drf_spectacular/openapi.py#L1385

        NOTE: The formatting has been kept the same as the original code.
        """

        if isinstance(serializer, OpenApiResponse):
            serializer, description, examples = (
                serializer.response, serializer.description, serializer.examples
            )
        else:
            description, examples = '', []

        serializer = force_instance(serializer)
        headers = self._get_response_headers_for_code(status_code, direction)
        headers = {'headers': headers} if headers else {}

        if not serializer:
            return {**headers, 'description': description or _('No response body')}
        elif is_list_serializer(serializer):
            schema = self._unwrap_list_serializer(serializer.child, direction)
            if not schema:
                return {**headers, 'description': description or _('No response body')}
        elif is_serializer(serializer):
            component = self.resolve_serializer(serializer, direction)
            if not component:
                return {**headers, 'description': description or _('No response body')}
            schema = component.ref
        elif is_basic_type(serializer):
            schema = build_basic_type(serializer)
        elif isinstance(serializer, dict):
            # bypass processing and use given schema directly
            schema = serializer
            # prevent invalid dict case in _is_list_view() as this not a status_code dict.
            serializer = None
        else:
            warn(
                f'could not resolve "{serializer}" for {self.method} {self.path}. Expected either '
                f'a serializer or some supported override mechanism. Defaulting to '
                f'generic free-form object.'
            )
            schema = build_basic_type(OpenApiTypes.OBJECT)
            schema['description'] = _('Unspecified response body')

        if (
            self._is_list_view(serializer)
            and get_override(serializer, 'many') is not False
            and ('200' <= status_code < '300' or spectacular_settings.ENABLE_LIST_MECHANICS_ON_NON_2XX)
        ):
            # In case of a non-default ListSerializer, check for matching extension and
            # bypass regular list wrapping by delegating handling to extension.
            if (
                is_list_serializer_customized(serializer)
                and OpenApiSerializerExtension.get_match(get_list_serializer(serializer))
            ):
                schema = self._map_serializer(get_list_serializer(serializer), direction)
            else:
                schema = build_array_type(schema)

            paginator = self._get_paginator()

            if (
                paginator
                and is_serializer(serializer)
                and (not is_list_serializer(serializer) or is_serializer(serializer.child))
            ):
                paginated_name = self.get_paginated_name(self._get_serializer_name(serializer, "response"))
                component = ResolvedComponent(
                    name=paginated_name,
                    type=ResolvedComponent.SCHEMA,
                    schema=paginator.get_paginated_response_schema(schema),
                    object=serializer.child if is_list_serializer(serializer) else serializer,
                )
                self.registry.register_on_missing(component)
                schema = component.ref
            elif paginator:
                schema = paginator.get_paginated_response_schema(schema)
            # ---
            # NOTE: This is custom functionality to ensure that non paginated
            # views that are list views get a list component as well even
            # though they are not paginated, this is primarily to ensure the
            # envelope names are unique.
            elif isinstance(self.view, BaseAPIView) and not paginator:
                paginated_name = "{}List".format(
                    self._get_serializer_name(serializer, "response")
                )
                component = ResolvedComponent(
                    name=paginated_name,
                    type=ResolvedComponent.SCHEMA,
                    schema=schema,
                    object=serializer
                )
                self.registry.register_on_missing(component)
                schema = component.ref
            # ---

        # ---
        # NOTE: This is custom functionality to ensure BaseAPIView is correctly
        # enveloped in the response.
        # Try and get a `paginated_name` variable to manually specify the
        # envelope_name.
        try:
            serializer_name = paginated_name
        except Exception:
            serializer_name = None
        # Get an envelope component.
        envelope = self._get_envelope(
            schema, serializer, direction, serializer_name=serializer_name
        )
        # If an envelope exists, then set it's reference on the schema.
        if envelope:
            schema = envelope.ref
        # ---

        if not media_types:
            media_types = self.map_renderers('media_type')

        media_types = modify_media_types_for_versioning(self.view, media_types)

        return {
            **headers,
            'content': {
                media_type: build_media_type_object(
                    schema,
                    self._get_examples(serializer, direction, media_type, status_code, examples)
                )
                for media_type in media_types
            },
            'description': description
        }

    def get_operation_id(self):
        """
        Override the operation ID with a custom one if needed (retrieved from
        the additional docs object),
        """

        operation_id_override = self._get_attr_from_view_docs("operationId")

        if operation_id_override:
            return operation_id_override

        return super().get_operation_id()

    def get_description(self):
        """
        Override the description with a custom one if needed (retrieved from the
        additional docs object).

        Also ensures that docstirngs are not used for view descriptions.
        """

        description_override = self._get_attr_from_view_docs("description")

        if description_override:
            return description_override

        return None

    def get_summary(self):
        """
        Override the summary with a custom one if needed (retrieved from the
        additional docs object).
        """

        summary_override = self._get_attr_from_view_docs("summary")

        if summary_override:
            return summary_override

        return super().get_summary()

    def is_deprecated(self):
        """
        Override the deprecated state with custom behaviour if needed (retrieved
        from the additional docs object).
        """

        deprecated_override = self._get_attr_from_view_docs("deprecated")

        if deprecated_override:
            return deprecated_override

        return super().is_deprecated()

    def get_extensions(self):
        """
        Override the extensions with custom ones if needed (retrieved from the
        additional docs object).

        Currently supports:
            - x-code-samples
        """

        extensions = {}

        x_code_samples = self._get_attr_from_view_docs("x-code-samples")

        if x_code_samples:
            extensions["x-code-samples"] = x_code_samples

        return extensions

    def get_response_serializers(self):
        """
        Use the correct response serializer and status code if a custom one is
        configured via a BaseAPIView.
        """

        # Customized response serializer handling if it is not a BaseAPIView.
        if not isinstance(self.view, BaseAPIView):
            return super().get_response_serializers()

        serializer = self.view.get_response_serializer()
        status_code = self.view.get_response_status_code()

        return {status_code: serializer}
