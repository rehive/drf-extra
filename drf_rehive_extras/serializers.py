from rest_framework import serializers
from rest_flex_fields import FlexFieldsModelSerializer


class BaseModelSerializer(FlexFieldsModelSerializer):
    pass


class ActionResponseSerializer(serializers.Serializer):
    """
    This serializer can be used if only a `status` is required in the response.
    """

    status = serializers.CharField(default="sucess")
