from rest_framework import serializers
from .models import Qualification

class QualificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Qualification
        fields = '__all__'
        read_only_fields = ('broker',)
