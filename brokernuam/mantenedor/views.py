from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from .models import Qualification, AuditLog, Broker
from .forms import QualificationForm, QualificationAmountsForm, BulkLoadForm
from decimal import Decimal, InvalidOperation
import csv
import io
from datetime import datetime
from django.contrib.auth.forms import UserCreationForm
from django.views.generic import CreateView
from django.urls import reverse_lazy

# --- LÓGICA DE NEGOCIO Y PARSEO (Trasplantado) ---
# Funciones extraídas de tu 'views.py' y el de tu compañero

def _to_float_safe(value):
    """
    Intenta convertir un valor a Decimal. Devuelve 0.0 si falla.
    Extraído de la lógica de carga masiva de tu compañero.
    """
    if value is None:
        return Decimal('0.0')
    try:
        # Reemplazar comas por puntos si es necesario (formato CSV)
        cleaned_value = str(value).strip().replace(',', '.')
        if cleaned_value == '':
            return Decimal('0.0')
        return Decimal(cleaned_value)
    except (InvalidOperation, ValueError):
        return Decimal('0.0')

def parse_csv(csv_file):
    """
    Parsea un archivo CSV en memoria y lo convierte en una lista de diccionarios.
    Extraído del views.py de tu compañero.
    """
    data = []
    try:
        decoded_file = csv_file.read().decode('utf-8-sig')
        io_string = io.StringIO(decoded_file)
        # Lee la primera línea para detectar el delimitador (ej. ; o ,)
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(io_string.read(1024))
        io_string.seek(0)
        
        reader = csv.reader(io_string, dialect=dialect)
        
        header = [h.strip() for h in next(reader)]
        
        for row in reader:
            if not any(row):  # Omitir filas vacías
                continue
            data.append(dict(zip(header, row)))
            
    except Exception as e:
        raise ValueError(f"Error al parsear el CSV: {e}")
    return data

def CalculoFactores(montos_data):
    """
    Lógica de negocio principal para convertir Montos a Factores.
    Extraído y adaptado del views.py de tu compañero.
    
    Valida que la suma de factores 8-16 no exceda 1.
    """
    
    # 1. Convertir todos los montos a Decimal
    monto = {}
    for i in range(1, 30):
        # Asume que montos_data usa 'amount1', 'amount2', etc. para CRUD
        # o 'MSJ 1948 - C1' para carga masiva
        key_crud = f'amount{i}'
        key_csv = f'MSJ 1948 - C{i}'
        
        if key_crud in montos_data:
            monto[i] = _to_float_safe(montos_data.get(key_crud, 0))
        elif key_csv in montos_data:
             monto[i] = _to_float_safe(montos_data.get(key_csv, 0))
        else:
            monto[i] = Decimal('0.0')

    factores = {}
    
    # Asegurarse de que el monto1 (Divisor) no sea cero
    divisor = monto[1]
    if divisor == Decimal('0.0'):
        # Si el monto 1 es cero, todos los factores calculados son cero
        for i in range(8, 30):
            factores[f'factor{i}'] = Decimal('0.0')
        return factores # Retorna factores en cero (pasa la validación)

    # 2. Lógica de cálculo (basada en el views.py de tu compañero)
    factores['factor8'] = (monto[8] + monto[9] + monto[10] + monto[11] + monto[12] + monto[13]) / divisor
    factores['factor9'] = (monto[14] + monto[15]) / divisor
    factores['factor10'] = (monto[16] + monto[17] + monto[18]) / divisor
    factores['factor11'] = (monto[19] + monto[20] + monto[21]) / divisor
    factores['factor12'] = (monto[22] + monto[23]) / divisor
    factores['factor13'] = monto[24] / divisor
    factores['factor14'] = monto[25] / divisor
    factores['factor15'] = monto[26] / divisor
    factores['factor16'] = (monto[27] + monto[28]) / divisor
    
    # Factores 17-29 son copia directa de montos
    for i in range(17, 30):
        factores[f'factor{i}'] = monto[i]

    # 3. Validación (basada en el views.py de tu compañero)
    suma_factores_8_16 = sum(factores.get(f'factor{i}', Decimal('0.0')) for i in range(8, 17))
    
    if round(suma_factores_8_16, 4) > 1:
        raise ValueError("La suma de factores 8 a 16 excede 1")

    return factores

# --- VISTAS ---

class QualificationListView(LoginRequiredMixin, ListView):
    model = Qualification
    template_name = 'mantenedor/qualification_list.html'
    context_object_name = 'qualifications'

    def get_queryset(self):
        """
        Sobrescrito para implementar segregación de datos y manejo de superusuarios.
        """
        queryset = super().get_queryset()

        if hasattr(self.request.user, 'userprofile'):
            # Usuario normal con perfil de corredor
            broker = self.request.user.userprofile.broker
            
            # Obtener datos base de la bolsa (is_bolsa=True)
            bolsa_qs = queryset.filter(is_bolsa=True)
            # Obtener datos específicos del corredor
            broker_qs = queryset.filter(broker=broker)

            # Lógica de "override": Los datos del corredor pisan a los de la bolsa
            combined = {}
            # 1. Cargar datos de la bolsa
            for q in bolsa_qs:
                key = (q.mercado, q.instrumento, q.fecha_pago, q.ejercicio)
                combined[key] = q
            # 2. Sobrescribir con datos del corredor
            for q in broker_qs:
                key = (q.mercado, q.instrumento, q.fecha_pago, q.ejercicio)
                combined[key] = q
            
            return list(combined.values())
        
        elif self.request.user.is_superuser:
            # Superadmin (sin perfil de corredor), que vea todo
            return queryset.all()
        
        else:
            # Caso anómalo: usuario logueado sin perfil, no debe ver nada
            return queryset.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BulkLoadForm()
        return context

@login_required
def create_qualification(request):
    """
    Vista para crear una nueva calificación (CRUD).
    Implementa la lógica de cálculo real.
    """
    if request.method == 'POST':
        form = QualificationForm(request.POST)
        amounts_form = QualificationAmountsForm(request.POST)
        
        if form.is_valid() and amounts_form.is_valid():
            qualification = form.save(commit=False)
            qualification.broker = request.user.userprofile.broker
            qualification.origen = 'Manual'
            
            montos_data = amounts_form.cleaned_data
            # Guardar montos en JSON (convertir Decimal a string)
            qualification.montos = {k: str(v if v is not None else '0.0') for k, v in montos_data.items()}

            try:
                # --- LÓGICA DE NEGOCIO REAL ---
                factores_calculados = CalculoFactores(montos_data)
                qualification.factores = {k: str(v) for k, v in factores_calculados.items()}
                # --- FIN ---
                
                qualification.save() # Guardar el objeto completo
                
                AuditLog.objects.create(
                    user=request.user,
                    action='create',
                    qualification=qualification,
                    details=f"Creación manual de {qualification.instrumento}"
                )
                messages.success(request, 'Calificación creada exitosamente.')
                return redirect('qualification_list')
                
            except ValueError as e:
                # Capturar el error de validación de CalculoFactores (ej. Suma > 1)
                messages.error(request, f"Error de validación: {e}")
        
        else:
            messages.error(request, 'Formulario inválido.')
    else:
        form = QualificationForm()
        amounts_form = QualificationAmountsForm()

    return render(request, 'mantenedor/qualification_form.html', {
        'form': form,
        'amounts_form': amounts_form,
        'action': 'Crear'
    })

@login_required
def update_qualification(request, pk):
    """
    Vista para actualizar una calificación existente (CRUD).
    Implementa la lógica de cálculo real.
    """
    qualification = get_object_or_404(Qualification, pk=pk, broker=request.user.userprofile.broker)
    
    if request.method == 'POST':
        form = QualificationForm(request.POST, instance=qualification)
        amounts_form = QualificationAmountsForm(request.POST)
        
        if form.is_valid() and amounts_form.is_valid():
            qualification = form.save(commit=False)
            
            montos_data = amounts_form.cleaned_data
            qualification.montos = {k: str(v if v is not None else '0.0') for k, v in montos_data.items()}

            try:
                # --- LÓGICA DE NEGOCIO REAL ---
                factores_calculados = CalculoFactores(montos_data)
                qualification.factores = {k: str(v) for k, v in factores_calculados.items()}
                # --- FIN ---

                qualification.save() # Guardar cambios
                
                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    qualification=qualification,
                    details=f"Actualización manual de {qualification.instrumento}"
                )
                messages.success(request, 'Calificación actualizada exitosamente.')
                return redirect('qualification_list')

            except ValueError as e:
                messages.error(request, f"Error de validación: {e}")
        
        else:
            messages.error(request, 'Formulario inválido.')
    else:
        form = QualificationForm(instance=qualification)
        # Cargar montos existentes si los hay
        initial_amounts = {k: Decimal(v) for k, v in qualification.montos.items()} if qualification.montos else {}
        amounts_form = QualificationAmountsForm(initial=initial_amounts)

    return render(request, 'mantenedor/qualification_form.html', {
        'form': form,
        'amounts_form': amounts_form,
        'action': 'Actualizar'
    })

class QualificationDeleteView(LoginRequiredMixin, DeleteView):
    model = Qualification
    template_name = 'mantenedor/qualification_confirm_delete.html'
    success_url = reverse_lazy('qualification_list')

    def get_queryset(self):
        # Asegurar que solo el corredor dueño pueda borrar
        return super().get_queryset().filter(broker=self.request.user.userprofile.broker)

    def form_valid(self, form):
        # Log de auditoría ANTES de borrar
        qualification = self.get_object()
        AuditLog.objects.create(
            user=self.request.user,
            action='delete',
            details=f"Eliminación de {qualification.instrumento} (ID: {qualification.pk})"
        )
        messages.success(self.request, 'Calificación eliminada exitosamente.')
        return super().form_valid(form)

@login_required
@transaction.atomic # Si una fila falla, toda la carga falla
def bulk_load(request):
    """
    Vista para la carga masiva (CSV) de Montos o Factores.
    Implementa la lógica de cálculo real para 'montos'.
    """
    if request.method != 'POST':
        return redirect('qualification_list')

    form = BulkLoadForm(request.POST, request.FILES)
    
    if form.is_valid():
        csv_file = request.FILES['csv_file']
        load_type = form.cleaned_data['load_type']
        
        try:
            parsed_data = parse_csv(csv_file)
            created_count = 0
            updated_count = 0
            broker = request.user.userprofile.broker
            
            for row in parsed_data:
                # --- 1. Parsear datos comunes y clave única ---
                fecha_pago_str = row.get('fecha_pago')
                if not fecha_pago_str:
                    raise ValueError(f"Fila sin fecha_pago: {row.get('instrumento')}")
                
                try:
                    # Intentar formatos comunes
                    fecha_pago = datetime.strptime(fecha_pago_str, '%d/%m/%Y').date()
                except ValueError:
                    try:
                        fecha_pago = datetime.strptime(fecha_pago_str, '%Y-%m-%d').date()
                    except ValueError:
                        raise ValueError(f"Formato de fecha inválido '{fecha_pago_str}' en fila: {row.get('instrumento')}")

                unique_key = {
                    'broker': broker,
                    'mercado': row.get('mercado'),
                    'instrumento': row.get('instrumento'),
                    'fecha_pago': fecha_pago,
                    'ejercicio': int(_to_float_safe(row.get('ejercicio', 0)))
                }
                
                # Omitir filas sin datos clave
                if not all(unique_key.values()):
                    continue 

                defaults = {'origen': f'Carga Masiva - {load_type}'}
                
                # --- 2. Procesar según el tipo de carga ---
                if load_type == 'montos':
                    # Extraer montos usando la cabecera 'MSJ 1948 - Ci'
                    montos_data = {f'amount{i}': _to_float_safe(row.get(f'MSJ 1948 - C{i}')) for i in range(1, 30)}
                    
                    # Calcular factores
                    factores_data = CalculoFactores(montos_data)
                    
                    defaults['montos'] = {k: str(v) for k, v in montos_data.items()}
                    defaults['factores'] = {k: str(v) for k, v in factores_data.items()}

                else: # 'factores'
                    # Extraer factores
                    factores_data = {f'factor{i}': _to_float_safe(row.get(f'factor{i}')) for i in range(1, 30)}
                    
                    # Validar suma (8-16)
                    suma_factores_8_16 = sum(factores_data.get(f'factor{i}', Decimal('0.0')) for i in range(8, 17))
                    if round(suma_factores_8_16, 4) > 1:
                        raise ValueError(f"Error en fila {row.get('instrumento')}: La suma de factores 8 a 16 excede 1")
                    
                    defaults['factores'] = {k: str(v) for k, v in factores_data.items()}
                    defaults['montos'] = {} # No hay montos

                # --- 3. Guardar en la BD ---
                qual, created = Qualification.objects.update_or_create(
                    **unique_key,
                    defaults=defaults
                )
                
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            
            # --- 4. Log y Mensaje de éxito ---
            AuditLog.objects.create(
                user=request.user,
                action='bulk_load',
                details=f"Carga Masiva '{load_type}': {created_count} creadas, {updated_count} actualizadas."
            )
            messages.success(request, f"Carga masiva completada: {created_count} creadas, {updated_count} actualizadas.")
        
        except Exception as e:
            messages.error(request, f"Error en la carga: {e}")
            
    return redirect('qualification_list')

# --- VISTA DE SIGNUP AÑADIDA ---

class SignUpView(CreateView):
    """
    Vista para registrar nuevos usuarios.
    Usa el formulario estándar de Django. La señal en models.py
    se encargará de crear el UserProfile y asignarlo al 'Default Broker'.
    """
    form_class = UserCreationForm
    success_url = reverse_lazy('login') # Redirige al login después de crear la cuenta
    template_name = 'registration/signup.html'

    def form_valid(self, form):
        messages.success(self.request, 'Cuenta creada exitosamente. Ahora puedes iniciar sesión.')
        return super().form_valid(form)

# --- FIN ---