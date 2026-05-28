from rest_framework import serializers
from .models import SharePointConfig, SharePointSyncLog

class SharePointConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharePointConfig
        fields = '__all__'


class SharePointSyncLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SharePointSyncLog
        fields = '__all__'
