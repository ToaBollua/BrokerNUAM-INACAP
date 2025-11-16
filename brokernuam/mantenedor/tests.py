from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Broker, Qualification
from django.core.files.uploadedfile import SimpleUploadedFile
from decimal import Decimal

class MantenedorTests(TestCase):

    def setUp(self):
        """
        Configura un entorno de prueba aislado con dos corredores y dos usuarios.
        """
        # 1. Crear Corredores
        self.broker_a = Broker.objects.create(name="Corredora Alfa")
        self.broker_b = Broker.objects.create(name="Corredora Beta")

        # 2. Crear Usuarios (la señal en models.py creará UserProfile)
        self.user_a = User.objects.create_user(username='user_a', password='password_a')
        self.user_b = User.objects.create_user(username='user_b', password='password_b')

        # 3. Corregir la asignación del Broker (la señal los asigna a 'Default')
        profile_a = self.user_a.userprofile
        profile_a.broker = self.broker_a
        profile_a.save()

        profile_b = self.user_b.userprofile
        profile_b.broker = self.broker_b
        profile_b.save()

        # 4. Crear Clientes de Test (logueados)
        self.client_a = Client()
        self.client_b = Client()
        self.client_a.login(username='user_a', password='password_a')
        self.client_b.login(username='user_b', password='password_b')

        # 5. Crear dato de prueba para Corredor A
        self.qual_a = Qualification.objects.create(
            broker=self.broker_a,
            mercado='acciones',
            instrumento='TEST-ALFA',
            fecha_pago='2025-01-01',
            ejercicio=2025,
            origen='Test'
        )

    def test_autenticacion_requerida(self):
        """
        Prueba que la vista principal redirige a los usuarios no autenticados.
        """
        client = Client() # Cliente anónimo
        response = client.get(reverse('qualification_list'))
        # 302 = Redirección a la página de login
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_segregacion_lista_vista(self):
        """
        Prueba que el Corredor A solo ve sus datos y el Corredor B solo los suyos.
        """
        # El Corredor A debe ver su calificación
        response_a = self.client_a.get(reverse('qualification_list'))
        self.assertEqual(response_a.status_code, 200)
        self.assertContains(response_a, 'TEST-ALFA')

        # El Corredor B NO debe ver la calificación de A
        response_b = self.client_b.get(reverse('qualification_list'))
        self.assertEqual(response_b.status_code, 200)
        self.assertNotContains(response_b, 'TEST-ALFA')

    def test_segregacion_acceso_edicion(self):
        """
        Prueba que el Corredor B no puede acceder a la URL de edición del Corredor A.
        """
        url_edicion_a = reverse('update_qualification', args=[self.qual_a.pk])
        
        # El Corredor B intenta acceder
        response_b = self.client_b.get(url_edicion_a)
        
        # La vista usa get_object_or_404(..., broker=user.broker), por lo que debe fallar
        self.assertEqual(response_b.status_code, 404)

    def test_segregacion_acceso_eliminacion(self):
        """
        Prueba que el Corredor B no puede acceder a la URL de eliminación del Corredor A.
        """
        url_delete_a = reverse('delete_qualification', args=[self.qual_a.pk])
        response_b = self.client_b.get(url_delete_a)
        self.assertEqual(response_b.status_code, 404)

    def test_validacion_suma_factores_falla(self):
        """
        Prueba que la vista de actualización rechaza montos si los factores resultantes (8-16) suman más de 1.
        """
        url_update = reverse('update_qualification', args=[self.qual_a.pk])
        
        # Datos base de la calificación
        post_data = {
            'mercado': self.qual_a.mercado,
            'instrumento': self.qual_a.instrumento,
            'fecha_pago': self.qual_a.fecha_pago,
            'ejercicio': self.qual_a.ejercicio,
            'origen': self.qual_a.origen, # Campo que faltaba en el test anterior
        }
        
        # --- CORRECCIÓN ---
        # Añadir un divisor válido (amount1) para que el cálculo se ejecute
        post_data['amount1'] = 100 
        
        # Añadir montos que (divididos por 100) suman > 1
        for i in range(2, 30): # Empezar desde 2
            post_data[f'amount{i}'] = 0
        
        # Lógica de cálculo: factor8 = (monto[8]...monto[13]) / divisor
        # (50 + 60) / 100 = 1.1
        post_data['amount8'] = 50 
        post_data['amount9'] = 60
        # Suma = 1.1
        
        response = self.client_a.post(url_update, data=post_data)
        
        # Debe fallar la validación y recargar la página
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'La suma de factores 8 a 16 excede 1')

    def test_carga_masiva_factores_csv(self):
        """
        Prueba la carga masiva usando el archivo CSV proporcionado.
        """
        # Contenido del CSV
        csv_content = """mercado,instrumento,fecha_pago,ejercicio,factor1,factor2,factor3,factor4,factor5,factor6,factor7,factor8,factor9,factor10,factor11,factor12,factor13,factor14,factor15,factor16
acciones,TEST-CSV-001,15/11/2025,2025,1,0,0,0,0,0,0,0.1,0.1,0,0,0,0,0,0,0.1
cfi,TEST-CSV-002,16/11/2025,2025,0,1,0,0,0,0,0,0.2,0,0,0,0,0,0,0,0.1
"""
        # Crear un archivo en memoria para simular la subida
        csv_file = SimpleUploadedFile("test_carga.csv", csv_content.encode('utf-8'), content_type="text/csv")

        response = self.client_a.post(reverse('bulk_load'), {
            'csv_file': csv_file,
            'load_type': 'factores'
        })
        
        # Debe redirigir con éxito a la lista
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('qualification_list'))

        # Verificar que los datos existen y pertenecen al Corredor A
        self.assertTrue(Qualification.objects.filter(broker=self.broker_a, instrumento='TEST-CSV-001').exists())
        self.assertTrue(Qualification.objects.filter(broker=self.broker_a, instrumento='TEST-CSV-002').exists())
        
        # Verificar que el Corredor B no los ve
        response_b = self.client_b.get(reverse('qualification_list'))
        self.assertNotContains(response_b, 'TEST-CSV-001')