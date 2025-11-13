#
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
import pandas as pd
from .models import CalificacionTributaria
from .serializers import CalificacionTributariaSerializer

class CalificacionTributariaViewSet(viewsets.ModelViewSet):
    """
    API ViewSet para el CRUD (Épicas 1 y 2) y Carga Masiva (Épica 3).
    """
    serializer_class = CalificacionTributariaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Implementación del RNF-01: Segregación de Datos.
        Filtra obligatoriamente por el corredor del usuario logueado.
       
        """
        return CalificacionTributaria.objects.filter(corredor=self.request.user.corredor)

    def perform_create(self, serializer):
        """ Asigna automáticamente el Corredor y el Creador al guardar. """
        serializer.save(
            corredor=self.request.user.corredor,
            creado_por=self.request.user
        )

    def perform_update(self, serializer):
        """ Asigna automáticamente quién modificó el registro. """
        serializer.save(modificado_por=self.request.user)

    # --- NUEVO: Endpoint de Previsualización ---
    # Esto coincide con la llamada en tu FileUpload.js
    @action(detail=False, methods=['post'], url_path='previsualizar-csv')
    def previsualizar_csv(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No se subió ningún archivo'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Leemos solo las primeras 5 filas para la previsualización
            df = pd.read_csv(file, nrows=5)
            # Convertimos el dataframe a una lista de listas (JSON)
            preview_data = [df.columns.values.tolist()] + df.values.tolist()
            return Response({'preview': preview_data})
        except Exception as e:
            return Response({'error': f'Error procesando el archivo: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    # --- NUEVO: Endpoint de Carga Masiva ---
    #
    @action(detail=False, methods=['post'], url_path='carga-masiva')
    def carga_masiva(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No se subió ningún archivo'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_csv(file)
            
            # --- Aquí iría la lógica de cálculo de factores (RF-08) ---
            # Por ahora, asumimos que el CSV tiene los factores correctos.
            # Ejemplo: df['factor_8'] = df['monto_bruto'] * 0.10 
            # ---------------------------------------------------------
            
            registros_creados = 0
            registros_actualizados = 0

            for _, row in df.iterrows():
                # Implementación de RF-07: Actualizar si existe, crear si es nuevo
                #
                obj, created = CalificacionTributaria.objects.update_or_create(
                    # Llave única para identificar duplicados
                    corredor=request.user.corredor, # RNF-01 Multi-tenancy
                    instrumento=row['instrumento'],
                    fecha_pago=row['fecha_pago'],
                    defaults={
                        'factor_8': row['factor_8'],
                        # ... mapea aquí TODOS los demás factores del CSV ...
                        'creado_por': request.user,
                        'modificado_por': request.user,
                    }
                )
                
                if created:
                    registros_creados += 1
                else:
                    registros_actualizados += 1

            return Response({
                'status': 'Carga completada',
                'creados': registros_creados,
                'actualizados': registros_actualizados
            })
        except Exception as e:
            return Response({'error': f'Error procesando la carga: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)