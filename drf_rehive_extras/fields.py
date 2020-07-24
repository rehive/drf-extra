import re
from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class MetadataField(serializers.JSONField):
    """
    JSON field for metadata serialization.
    """

    def to_internal_value(self, data):
        data = super().to_internal_value(data)

        if data is None or not isinstance(data, dict):
            raise serializers.ValidationError(
                _('Invalid metadata. Must be a valid object.'))

        def _validate(obj):
            if not isinstance(obj, dict):
                return

            for k, v in obj.items():
                if (not re.match(r"^[a-zA-Z0-9\_]+$", k) or "__" in k):
                    raise serializers.ValidationError(
                        _("Invalid metadata key. May only contain alphanumeric"
                          " characters, numbers and single underscores.")
                    )
                _validate(v)

        _validate(data)

        return data


class TimestampField(serializers.Field):
    """
    Timestamp field for datetime serialization.
    """

    def __init__(self, *args, **kwargs):
        self.multiplier = kwargs.pop('multiplier', 1000)
        super().__init__(*args, **kwargs)

    def to_representation(self, obj):
        try:
            return int(obj.timestamp() * self.multiplier)
        except AttributeError:
            return None

    def to_internal_value(self, obj):
        try:
            date = datetime.strptime(str(obj), '%Y-%m-%dT%H:%M:%SZ').timestamp()
        except ValueError:
            raise serializers.ValidationError(
                _('Incorrect date format, expected ISO 8601.'))

        return datetime.fromtimestamp(int(date))


class EnumField(serializers.ChoiceField):
    def __init__(self, enum, **kwargs):
        self.enum = enum
        kwargs['choices'] = [(e.value, e.label) for e in enum]
        super().__init__(**kwargs)
    def to_representation(self, obj):
        try:
            return obj.value
        except AttributeError:
            return obj
    def to_internal_value(self, data):
        try:
            return self.enum(data)
        except ValueError:
            self.fail('invalid_choice', input=data)
