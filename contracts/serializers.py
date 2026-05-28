from rest_framework import serializers
from .models import Contract, RedlineSuggestion, ContractComparison

class ContractSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = '__all__'


class RedlineSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedlineSuggestion
        fields = '__all__'


class ContractComparisonSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractComparison
        fields = '__all__'
