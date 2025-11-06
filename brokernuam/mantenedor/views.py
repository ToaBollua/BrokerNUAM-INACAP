from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils.timezone import make_aware
from django.http import JsonResponse
import csv
import io
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from .models import Qualification, AuditLog, Broker
from .forms import QualificationForm, QualificationAmountsForm, QualificationFactorsForm, BulkLoadForm


# ------------ Utilidades ------------

def _json_safe(value):
    """Convierte recursivamente a tipos serializables por JSONSerializer."""
    if isinstance(value, (date, datetime)):
        # guardamos fecha/fecha-hora como ISO 8601
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return value


def _parse_date_any(s):
    """Intenta parsear múltiples formatos de fecha, devuelve date o None."""
    if not s:
        return None
    s = str(s).strip()
    # Intento ISO (YYYY-MM-DD)
    try:
        return date.fromisoformat(s)
    except Exception:
        pass
    # Intento DD/MM/YYYY
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except Exception:
        pass
    # Intento MM/DD/YYYY
    try:
        return datetime.strptime(s, "%m/%d/%Y").date()
    except Exception:
        pass
    return None


def _to_float_safe(v, default=0.0):
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        # intentar con Decimal por si viene con coma, etc.
        try:
            return float(Decimal(str(v).replace(",", ".")))
        except (InvalidOperation, ValueError, TypeError):
            return default


def _sum_range(d, prefix, start, end):
    """Suma d[f'{prefix}{i}'] para i en [start, end] como floats seguros."""
    total = 0.0
    for i in range(start, end + 1):
        total += _to_float_safe(d.get(f"{prefix}{i}", 0))
    return total


# ------------ Listado ------------

class QualificationListView(LoginRequiredMixin, ListView):
    model = Qualification
    template_name = 'mantenedor/qualification_list.html'
    context_object_name = 'qualifications'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        broker = self.request.user.userprofile.broker
        # Incluye datos de bolsa e incluye datos del broker, con prioridad broker
        bolsa_qs = queryset.filter(is_bolsa=True)
        broker_qs = queryset.filter(broker=broker)
        combined = {}
        for q in bolsa_qs:
            key = (q.mercado, q.instrumento, q.fecha_pago, q.ejercicio)
            combined[key] = q
        for q in broker_qs:
            key = (q.mercado, q.instrumento, q.fecha_pago, q.ejercicio)
            combined[key] = q
        # ListView acepta listas y la paginación funciona con listas
        return list(combined.values())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BulkLoadForm()
        return context


# ------------ Crear (flujo por pasos) ------------

@login_required
def create_qualification(request):
    if request.method == 'POST':
        step = request.POST.get('step', '1')

        # PASO 1: campos base (incluye fecha_pago, etc.)
        if step == '1':
            form = QualificationForm(request.POST)
            if form.is_valid():
                # Guardar en sesión de forma JSON-segura
                safe_data = _json_safe(form.cleaned_data)
                request.session['qualification_data'] = safe_data
                request.session.modified = True
                return render(request, 'mantenedor/create_step2.html', {
                    'form': QualificationAmountsForm()
                })
            else:
                return render(request, 'mantenedor/create_step1.html', {'form': form})

        # PASO 2: montos -> calcular factores (placeholder o fórmula real)
        elif step == '2':
            form = QualificationAmountsForm(request.POST)
            if form.is_valid():
                amounts = {k: _to_float_safe(v) for k, v in form.cleaned_data.items() if v is not None}
                qual_data = request.session.get('qualification_data', {})
                if not qual_data:
                    messages.error(request, 'La sesión del paso 1 expiró. Vuelve a iniciar el flujo.')
                    return redirect('qualification_create')  # ajusta al nombre real si corresponde

                qual_data['montos'] = amounts

                # Calcula factores (placeholder conservado, puedes reemplazar por el cálculo real)
                factores = {f'factor{i}': _to_float_safe(amounts.get(f'amount{i}', 0)) for i in range(1, 30)}

                # Validación: suma de factores 8..16 <= 1
                sum_f = _sum_range(factores, 'factor', 8, 16)
                if sum_f > 1.0 + 1e-9:
                    messages.error(request, 'La suma de factores 8 a 16 excede 1.')
                    return render(request, 'mantenedor/create_step2.html', {'form': form})

                qual_data['factores'] = factores
                # guardar de vuelta de forma segura
                request.session['qualification_data'] = _json_safe(qual_data)
                request.session.modified = True

                return render(request, 'mantenedor/create_step3.html', {'factores': factores})
            else:
                return render(request, 'mantenedor/create_step2.html', {'form': form})

        # PASO 3: persistir en BD
        elif step == '3':
            qual_data = request.session.get('qualification_data', {})
            if not qual_data:
                messages.error(request, 'La sesión expiró. Vuelve a iniciar la creación.')
                return redirect('qualification_create')

            broker = request.user.userprofile.broker

            # Convertir de vuelta tipos sensibles
            # fecha_pago viene como string ISO del paso 1; reconvertimos a date
            if 'fecha_pago' in qual_data:
                qual_data['fecha_pago'] = _parse_date_any(qual_data['fecha_pago'])

            # Campos JSON (montos, factores) ya están en tipos nativos serializables
            montos = qual_data.pop('montos', None)
            factores = qual_data.pop('factores', None)

            # Crear la calificación
            qual = Qualification.objects.create(
                broker=broker,
                **qual_data,
            )
            if montos is not None:
                qual.montos = montos
            if factores is not None:
                qual.factores = factores
            qual.save()

            AuditLog.objects.create(
                user=request.user,
                action='create',
                qualification=qual,
                details='Manual creation'
            )

            # Limpiar sesión para no contaminar futuros flujos
            try:
                del request.session['qualification_data']
            except KeyError:
                pass

            messages.success(request, 'Calificación creada correctamente.')
            return redirect('qualification_list')

        # Step desconocido
        messages.error(request, 'Paso inválido.')
        return redirect('qualification_create')

    # GET inicial
    form = QualificationForm(initial=request.session.get('qualification_data', {}))
    return render(request, 'mantenedor/create_step1.html', {'form': form})


# ------------ Actualizar ------------

@login_required
def update_qualification(request, pk):
    qual = get_object_or_404(Qualification, pk=pk, broker=request.user.userprofile.broker)
    if request.method == 'POST':
        form = QualificationForm(request.POST, instance=qual)
        amounts_form = QualificationAmountsForm(request.POST)
        if form.is_valid() and amounts_form.is_valid():
            amounts = {k: _to_float_safe(v) for k, v in amounts_form.cleaned_data.items() if v is not None}
            factores = {f'factor{i}': _to_float_safe(amounts.get(f'amount{i}', 0)) for i in range(1, 30)}

            sum_f = _sum_range(factores, 'factor', 8, 16)
            if sum_f > 1.0 + 1e-9:
                messages.error(request, 'La suma de factores 8 a 16 excede 1.')
                return render(request, 'mantenedor/update.html', {'form': form, 'amounts_form': amounts_form})

            qual = form.save()
            qual.montos = amounts
            qual.factores = factores
            qual.save()

            AuditLog.objects.create(
                user=request.user,
                action='update',
                qualification=qual,
                details='Manual update'
            )
            messages.success(request, 'Calificación actualizada correctamente.')
            return redirect('qualification_list')
        else:
            return render(request, 'mantenedor/update.html', {'form': form, 'amounts_form': amounts_form})
    else:
        form = QualificationForm(instance=qual)
        amounts_form = QualificationAmountsForm(initial=qual.montos or {})
    return render(request, 'mantenedor/update.html', {'form': form, 'amounts_form': amounts_form})


# ------------ Eliminar ------------

class QualificationDeleteView(LoginRequiredMixin, DeleteView):
    model = Qualification
    success_url = reverse_lazy('qualification_list')
    template_name = 'mantenedor/confirm_delete.html'

    def get_queryset(self):
        return super().get_queryset().filter(broker=self.request.user.userprofile.broker)

    def delete(self, request, *args, **kwargs):
        qual = self.get_object()
        AuditLog.objects.create(
            user=request.user,
            action='delete',
            qualification=qual,
            details='Manual delete'
        )
        messages.success(request, 'Calificación eliminada correctamente.')
        return super().delete(request, *args, **kwargs)


# ------------ Carga masiva ------------

@login_required
def bulk_load(request):
    if request.method == 'POST':
        form = BulkLoadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            load_type = form.cleaned_data['load_type']
            data = csv_file.read().decode('utf-8', errors='ignore')
            io_string = io.StringIO(data)
            reader = csv.DictReader(io_string)
            broker = request.user.userprofile.broker
            updated = 0
            created = 0

            with transaction.atomic():
                for row in reader:
                    mercado = (row.get('mercado') or '').strip()
                    instrumento = (row.get('instrumento') or '').strip()
                    fecha_pago = _parse_date_any(row.get('fecha_pago'))
                    try:
                        ejercicio = int((row.get('ejercicio') or '0').strip())
                    except ValueError:
                        ejercicio = 0

                    # Usar get_or_create con fecha date (no string)
                    qual, created_flag = Qualification.objects.get_or_create(
                        broker=broker,
                        mercado=mercado,
                        instrumento=instrumento,
                        fecha_pago=fecha_pago,
                        ejercicio=ejercicio,
                        defaults={'origen': f'Carga Masiva - {load_type.capitalize()}'}
                    )

                    if load_type == 'montos':
                        montos = {f'amount{i}': _to_float_safe(row.get(f'amount{i}', 0)) for i in range(1, 30)}
                        # placeholder: factores derivados de montos (ajusta con tu fórmula real)
                        factores = {f'factor{i}': _to_float_safe(row.get(f'amount{i}', 0)) for i in range(1, 30)}
                        qual.montos = montos
                        qual.factores = factores
                    else:
                        factores = {f'factor{i}': _to_float_safe(row.get(f'factor{i}', 0)) for i in range(1, 30)}
                        qual.factores = factores

                    qual.save()

                    if created_flag:
                        created += 1
                    else:
                        updated += 1

                    AuditLog.objects.create(
                        user=request.user,
                        action='bulk_load',
                        qualification=qual,
                        details=f'Bulk load {load_type}'
                    )

            messages.success(request, f'Carga masiva completada: {created} creadas, {updated} actualizadas.')
            return redirect('qualification_list')
    else:
        form = BulkLoadForm()
    return render(request, 'mantenedor/bulk_load.html', {'form': form})
