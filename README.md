<p align="center">
  <img width="64" src="https://avatars2.githubusercontent.com/u/22204821?s=200&v=4" alt="Rehive Logo">
  <h1 align="center">DRF Rehive Extras</h1>
  <p align="center">Extra utilities for using Django REST Framework.</p>
</p>

## Features

- Python >= 3.6
- Django >= 3.0
- Generic views and mixins for all CRUD.
- Custom pagination that supports cursor and page based pagination.
- Integrated support for flex fields and django filters.
- Base serializers.
- Metadata, timestamp, and enum serializer fields.
- Schema generation support via drf-spectacular.

## Getting started

1. Install the package:

```sh
pip install drf-rehive-extras
```

2. Add "drf_rehive_extras" to your `INSTALLED_APPS` settings like this:

```python
INSTALLED_APPS = [
    # ...
    'drf_rehive_extras',
]
```

## Usage

### Schema generation

This library allows you to use `drf-spectacular` to generate Open API schemas that match the Rehive eveloped request/response format as defined by the `drf-rehive-extras` views/serializers.

To use schema generation, install `drf-spectacular` (in addition to `drf-rehive-extras` as described above):

```sh
pip install drf-spectacular[sidecar]
```

And add the following to the `INSTALLED_APPS` settings:

```python
INSTALLED_APPS = [
    # ...
    'drf_spectacular',
    'drf_spectacular_sidecar',
]
```

Finally, configure the `REST_FRAMEWORK` settings with:

```python
REST_FRAMEWORK = {
  'DEFAULT_SCHEMA_CLASS': 'drf_rehive_extras.schema.BaseAutoSchema',
}
```

The `schema.BaseAutoSchema` class also includes functionality to attach
additional documentation to the schema via yaml files.

To generate additional documentation, create a `docs.yaml` file in a `docs` folder in your Django app. The file should be formatted like this:

```yaml
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
```

Then, in your `settings` file specify the above directory using the `ADDITIONAL_DOCS_DIRS` settings:

```python
import os

ADDITIONAL_DOCS_DIRS = [
    "/root/app/docs/",
]
```

### Pagination

This library adds extra pagination via `PageNumberPagination` and `CursorPagination` that can be used to generate paginated lists that return the results in the Rehive eveloped request/response format.

You can use them like this:

```python
from drf_rehive_extras.pagination import PageNumberPagination

class ExampleView(ListAPIView)
    pagination_class = PageNumberPagination
```

These pagination classes will be automatically applied to any views that inherit from the `drf-rehive-extras` generics and mixins.

### Serializers

This library includes base serializers that can be used to ensure all serializers share the same Rehive base:

- `BaseModelSerializer` : A DRF `ModelSerializer` that includes `rest_flex_fields` functionality.
- `ActionResponseSerializer` : A serializer that can be used to generate action responses.

### Serializers fields

This library adds extra serializer fields that can be used in DRF serializers:

- `MetadataField`
- `TimestampField`
- `EnumField`

These fields can be used like normal serializer fields.

### Views

This library includes a collection of generic views and mixins that can be used to ensure all views follow the same Rehive standard.

The generic views can be used like this:

```python
from drf_rehive_extras.generics import ListAPIView

class ListExampleModelView(ListAPIView):
    serializer_class = ExampleModelSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return ExampleModel.objects.none()

        return ExampleModel.objects.all().order_by('-created')
```

The generic views allow for the customization of the serializer based on the method. This can be done by adding a `serializer_classes` attribute to the view:

```python
# Single shared request/response serializer.
serializer_classes = {
    "POST": ExampleModelRequestSerializer
}

# Multiple serializers, the first for the request and the second for the response.
serializer_classes = {
    "POST": (ExampleModelRequestSerializer, ExampleModelResponseSerializer,)
}
```

The generic views also support explicitly modifying the response status for a given method. This can be done via the `response_status_codes` attribute.

```python
response_status_codes = {"POST": status.HTTP_202_ACCEPTED}
```

If possible, all generic views will attempt to add a `_resource` and `_resource_id` to the request object. This will only be done if there is a single model instance and the instance contains a `RESOURCE` and/or `RESOURCE_ID` attribute.

Finally, in addition to the normal DRF generic views, the library contains an extra `ActionAPIView` that can be used for simple actions. These actions will default to a 200 response and will only ever return a `{"status": "success"}` response.

Usage is as follows:

```python
from drf_rehive_extras.generics import ActionAPIView
from drf_rehive_extras.serializers import ActionResponseSerializer

class ExampleActionView(ActionAPIView):
    serializer_class = ExampleActionSerializer
    serializer_classes = {
        "POST": (ExampleActionSerializer, ActionResponseSerializer,)
    }
```
