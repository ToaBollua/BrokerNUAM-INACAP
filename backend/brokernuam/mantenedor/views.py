from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from .models import Qualification
from .serializers import QualificationSerializer
from .models import Qualification
from rest_framework import viewsets
from .serializers import QualificationSerializer

class QualificationViewSet(viewsets.ModelViewSet):
    queryset = Qualification.objects.all()  # <--- Este es el cambio principal
    serializer_class = QualificationSerializer

    def get_queryset(self):
        return Qualification.objects.filter(broker=self.request.user.userprofile.broker)




class QualificationViewSet(viewsets.ModelViewSet):
    serializer_class = QualificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Qualification.objects.filter(broker=self.request.user.userprofile.broker)

    def perform_create(self, serializer):
        serializer.save(broker=self.request.user.userprofile.broker)

    @action(detail=False, methods=['post'])
    def calcular_factores(self, request):
        montos = request.data.get('montos', {})
        factores = self.calculo_montos_a_factores(montos)
        if sum(factores[8:17]) > 1.0:  # del 8 al 16
            return Response({"error": "La suma de factores del 8 al 16 supera 1"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"factores": factores})

    def calculo_montos_a_factores(self, montos):
        factores = [0]*29
        total = sum(montos.values()) if montos else 1
        for i in range(29):
            factores[i] = float(montos.get(f"amount{i+1}", 0)) / total if total > 0 else 0
        return factores
