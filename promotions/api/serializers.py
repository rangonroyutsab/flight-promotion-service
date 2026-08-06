from rest_framework import serializers

class PromotionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    content = serializers.CharField()
    detail_url = serializers.CharField(required=False)
