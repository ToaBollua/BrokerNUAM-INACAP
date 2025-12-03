from django.test import TestCase
from django.contrib.auth.models import User
from .models import Broker, UserProfile, TaxQualification
import datetime

class MultiTenancyTestCase(TestCase):
    def setUp(self):
        # 1. Crear Escenario
        self.broker_a = Broker.objects.create(name="Broker Alpha", code="BRA")
        self.broker_b = Broker.objects.create(name="Broker Beta", code="BRB")
        
        self.user_a = User.objects.create_user(username="user_alpha", password="password123")
        UserProfile.objects.create(user=self.user_a, broker=self.broker_a)
        
        # 2. Crear Datos
        self.tax_a = TaxQualification.objects.create(
            broker=self.broker_a, 
            instrument="ACCION_DE_ALPHA", 
            payment_date=datetime.date.today(),
            exercise_year=2025
        )
        self.tax_b = TaxQualification.objects.create(
            broker=self.broker_b, 
            instrument="ACCION_DE_BETA", 
            payment_date=datetime.date.today(),
            exercise_year=2025
        )

    def test_data_segregation(self):
        """Validar que el Usuario A solo ve datos del Broker A"""
        print("\n--- EJECUTANDO TEST DE SEGREGACIÓN ---")
        queryset = TaxQualification.objects.filter(broker=self.user_a.userprofile.broker)
        
        self.assertIn(self.tax_a, queryset)
        self.assertNotIn(self.tax_b, queryset)
        print("✅ SEGREGACIÓN CONFIRMADA")