from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import JsonResponse
import csv
import io
from .models import Qualification, AuditLog, Broker
from .forms import QualificationForm, QualificationAmountsForm, QualificationFactorsForm, BulkLoadForm

class QualificationListView(LoginRequiredMixin, ListView):
    model = Qualification
    template_name = 'mantenedor/qualification_list.html'
    context_object_name = 'qualifications'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        broker = self.request.user.userprofile.broker
        # Include bolsa data and broker's data, with priority to broker
        bolsa_qs = queryset.filter(is_bolsa=True)
        broker_qs = queryset.filter(broker=broker)
        # Combine, broker overrides bolsa
        combined = {}
        for q in bolsa_qs:
            key = (q.mercado, q.instrumento, q.fecha_pago, q.ejercicio)
            combined[key] = q
        for q in broker_qs:
            key = (q.mercado, q.instrumento, q.fecha_pago, q.ejercicio)
            combined[key] = q
        return list(combined.values())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BulkLoadForm()
        return context

@login_required
def create_qualification(request):
    if request.method == 'POST':
        step = request.POST.get('step', '1')
        if step == '1':
            form = QualificationForm(request.POST)
            if form.is_valid():
                request.session['qualification_data'] = form.cleaned_data
                return render(request, 'mantenedor/create_step2.html', {'form': QualificationAmountsForm()})
        elif step == '2':
            form = QualificationAmountsForm(request.POST)
            if form.is_valid():
                amounts = {k: v for k, v in form.cleaned_data.items() if v is not None}
                qual_data = request.session.get('qualification_data')
                qual_data['montos'] = amounts
                # Calculate factors
                # Placeholder
                factores = {f'factor{i}': amounts.get(f'amount{i}', 0) for i in range(1, 30)}
                sum_f = sum(factores.get(f'factor{i}', 0) for i in range(8, 17))
                if sum_f > 1:
                    messages.error(request, 'Sum of factors 8 to 16 exceeds 1')
                    return render(request, 'mantenedor/create_step2.html', {'form': form})
                qual_data['factores'] = factores
                request.session['qualification_data'] = qual_data
                return render(request, 'mantenedor/create_step3.html', {'factores': factores})
        elif step == '3':
            # Save
            qual_data = request.session.get('qualification_data')
            broker = request.user.userprofile.broker
            qual = Qualification.objects.create(
                broker=broker,
                **qual_data
            )
            AuditLog.objects.create(
                user=request.user,
                action='create',
                qualification=qual,
                details='Manual creation'
            )
            messages.success(request, 'Qualification created successfully')
            return redirect('qualification_list')
    else:
        form = QualificationForm()
    return render(request, 'mantenedor/create_step1.html', {'form': form})

@login_required
def update_qualification(request, pk):
    qual = get_object_or_404(Qualification, pk=pk, broker=request.user.userprofile.broker)
    if request.method == 'POST':
        form = QualificationForm(request.POST, instance=qual)
        amounts_form = QualificationAmountsForm(request.POST)
        if form.is_valid() and amounts_form.is_valid():
            amounts = {k: v for k, v in amounts_form.cleaned_data.items() if v is not None}
            factores = {f'factor{i}': amounts.get(f'amount{i}', 0) for i in range(1, 30)}
            sum_f = sum(factores.get(f'factor{i}', 0) for i in range(8, 17))
            if sum_f > 1:
                messages.error(request, 'Sum of factors 8 to 16 exceeds 1')
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
            messages.success(request, 'Qualification updated successfully')
            return redirect('qualification_list')
    else:
        form = QualificationForm(instance=qual)
        amounts_form = QualificationAmountsForm(initial=qual.montos or {})
    return render(request, 'mantenedor/update.html', {'form': form, 'amounts_form': amounts_form})

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
        messages.success(request, 'Qualification deleted successfully')
        return super().delete(request, *args, **kwargs)

@login_required
def bulk_load(request):
    if request.method == 'POST':
        form = BulkLoadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            load_type = form.cleaned_data['load_type']
            data = csv_file.read().decode('utf-8')
            io_string = io.StringIO(data)
            reader = csv.DictReader(io_string)
            broker = request.user.userprofile.broker
            updated = 0
            created = 0
            with transaction.atomic():
                for row in reader:
                    # Assume columns: mercado, instrumento, fecha_pago, ejercicio, amount1..29 or factor1..29
                    qual, created_flag = Qualification.objects.get_or_create(
                        broker=broker,
                        mercado=row['mercado'],
                        instrumento=row['instrumento'],
                        fecha_pago=row['fecha_pago'],
                        ejercicio=int(row['ejercicio']),
                        defaults={'origen': f'Carga Masiva - {load_type.capitalize()}'}
                    )
                    if load_type == 'montos':
                        montos = {f'amount{i}': float(row.get(f'amount{i}', 0)) for i in range(1, 30)}
                        factores = {f'factor{i}': float(row.get(f'amount{i}', 0)) for i in range(1, 30)}  # placeholder
                        qual.montos = montos
                        qual.factores = factores
                    else:
                        factores = {f'factor{i}': float(row.get(f'factor{i}', 0)) for i in range(1, 30)}
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
            messages.success(request, f'Bulk load completed: {created} created, {updated} updated')
            return redirect('qualification_list')
    else:
        form = BulkLoadForm()
    return render(request, 'mantenedor/bulk_load.html', {'form': form})
