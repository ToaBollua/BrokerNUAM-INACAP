from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AuditLog, TaxQualification, Broker, UserProfile
from django.http import HttpResponse
from .resources import TaxQualificationResource
from datetime import datetime
from django.shortcuts import redirect
from .forms import ManualEntryForm, CSVUploadForm
import csv
import io
import json

# --- VISTA DASHBOARD (CON MULTI-TENANCY) ---
@login_required
def home(request):
    """
    Dashboard principal con SEGREGACIÓN DE DATOS (Multi-tenancy).
    Muestra datos filtrados según el perfil del usuario (Admin vs Corredor).
    """
    user = request.user
    
    # 1. Determinar el Broker del usuario
    try:
        user_broker = user.userprofile.broker
    except:
        user_broker = None

    # 2. Filtrar Calificaciones
    if user.is_superuser:
        # El admin ve todo (Modo Dios)
        qualifications = TaxQualification.objects.all().order_by('-created_at')[:20]
        broker_name = "ADMINISTRADOR GLOBAL"
    elif user_broker:
        # El usuario normal SOLO ve lo de su broker
        qualifications = TaxQualification.objects.filter(broker=user_broker).order_by('-created_at')[:20]
        broker_name = user_broker.name
    else:
        # Usuario huérfano (sin broker asignado)
        qualifications = []
        broker_name = "SIN ASIGNACIÓN (Contacte a Soporte)"

    # 3. Filtrar Logs (¿Quién hizo qué?)
    # El admin ve todo el historial; el usuario solo ve sus propias acciones.
    if user.is_superuser:
        logs = AuditLog.objects.all().order_by('-timestamp')[:50]
    else:
        logs = AuditLog.objects.filter(user=user).order_by('-timestamp')[:20]
    
    context = {
        'logs': logs,
        'qualifications': qualifications,
        'user': user,
        'broker_name': broker_name
    }
    return render(request, 'index.html', context)

# --- VISTA DE CARGA CSV ---
@login_required
def upload_csv(request):
    """Procesa la carga masiva de archivos CSV."""
    if request.method == 'POST':
        form = CsvUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            
            # TODO: Aquí iría la lógica de parsing con Pandas/CSV.
            # Por ahora registramos la acción para cumplir con la auditoría.
            
            # 1. Registrar Auditoría
            AuditLog.objects.create(
                user=request.user,
                action='UPLOAD_CSV',
                details=f"Archivo cargado: {csv_file.name} ({csv_file.size} bytes)"
            )
            
            messages.success(request, f"Archivo {csv_file.name} procesado correctamente.")
        else:
            messages.error(request, "Error en el formulario de carga.")
    
    return redirect('home')

# --- VISTA DE ACTUALIZACIÓN DE FACTOR ---
@login_required
def update_factor(request):
    """Actualiza un factor específico manualmente."""
    if request.method == 'POST':
        form = FactorUpdateForm(request.POST)
        if form.is_valid():
            broker_code = form.cleaned_data['broker_code']
            new_factor = form.cleaned_data['new_factor']
            
            # Aquí conectaríamos con el modelo TaxQualification para actualizar el valor real.
            
            # Registrar Auditoría
            AuditLog.objects.create(
                user=request.user,
                action='UPDATE_FACTOR',
                details=f"Factor actualizado para Broker {broker_code}: {new_factor}"
            )
            
            messages.success(request, f"Factor actualizado para {broker_code}.")
        else:
            messages.error(request, "Datos inválidos para actualización de factor.")
            
    return redirect('home')


@login_required
def export_users_data(request):
    # 1. SEGURIDAD: Obtener el broker del usuario actual
    try:
        user_broker = request.user.userprofile.broker
    except:
        return HttpResponse("Error: Usuario sin perfil de corredor asignado.", status=403)

    # 2. FILTRADO: Obtener solo los datos de ESTE corredor (Multi-tenancy)
    dataset = TaxQualificationResource().export(
        queryset=TaxQualification.objects.filter(broker=user_broker)
    )

    # 3. RESPUESTA: Generar archivo Excel (.xlsx)
    response = HttpResponse(dataset.xlsx, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    # Nombre del archivo dinámico: "reporte_LarrainVial_2025-12-10.xlsx"
    filename = f"reporte_{user_broker.code}_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@login_required
def manual_entry(request):
    if request.method == 'POST':
        form = ManualEntryForm(request.POST)
        if form.is_valid():
            qualification = form.save(commit=False)
            # Asignar automáticamente el Broker del usuario (SEGURIDAD)
            qualification.broker = request.user.userprofile.broker
            qualification.save()
            return redirect('home')
    else:
        form = ManualEntryForm()
    
    return render(request, 'manual_entry.html', {'form': form})

@login_required
def upload_csv(request):
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            for row in reader:
                # Usamos update_or_create para evitar duplicados (IntegrityError)
                TaxQualification.objects.update_or_create(
                    # 1. Campos para BUSCAR si ya existe (La clave única)
                    broker=request.user.userprofile.broker,
                    instrument=row.get('instrument', 'Unknown'),
                    payment_date=row.get('payment_date', '2024-01-01'),
                    
                    # 2. Campos para ACTUALIZAR o CREAR
                    defaults={
                        'exercise_year': int(row.get('exercise_year', 2024)),
                        'source': 'CSV',
                        'financial_data': json.loads(row.get('financial_data', '{}'))
                    }
                )
            return redirect('home')
    else:
        form = CSVUploadForm()
    
    return render(request, 'upload_csv.html', {'form': form})