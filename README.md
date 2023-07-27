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
- Metadata, timestamp and enum serializer fields.


## Getting started

1. Install the package:

```sh
pip install drf-rehive-extras
```

2. Add "drf_rehive_extras" to your `INSTALLED_APPS` settings like this:

```python
INSTALLED_APPS = [
    ...
    'drf_rehive_extras',
]
```

## Usage

### Schema generation

Use drf-spectacular to generate Open API schemas that match the Rehive eveloped request response format as defined by the drf-rehive-extras views/serializers.

To use schema generation, install `drf-spectacular`:

```sh
pip install drf-spectacular[sidecar]
```

And add the following to the `INSTALLED_APPS` settings:

```python
INSTALLED_APPS = [
    ...
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

Additionally, the `schema.BaseAutoSchema` class includes functionality to attach
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

the `PageNumberPagination` and `CursorPagination` can be used to generate paginated lists that return the results enveloped in a parent `data` object (as per the Rehive standard).

You can use them like this:

```python
from drf_rehive_extras.pagination import PageNumberPagination

class ExampleView(ListAPIView)
    pagination_class = PageNumberPagination

```

These pagination classes will be automatically applied to any views that inherit from the `drf-rehive-extras` generics and mixins.

### Serializers


### Serializers fields


### Views
