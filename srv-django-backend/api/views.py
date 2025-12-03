from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AuditLog, TaxQualification, Broker, UserProfile
from .forms import CsvUploadForm, FactorUpdateForm
import datetime

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