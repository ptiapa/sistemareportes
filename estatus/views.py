from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import EstatusSemanal
from .forms import EstatusSemanalForm
import pandas as pd


# 🟦 Listar estatus con filtros, orden y exportación a Excel
def lista_estatus(request):
    estatus = EstatusSemanal.objects.all().order_by('-fecha')

    # Filtros por fecha
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    orden = request.GET.get('orden')

    if fecha_inicio:
        estatus = estatus.filter(fecha__gte=fecha_inicio)
    if fecha_fin:
        estatus = estatus.filter(fecha__lte=fecha_fin)

    # Ordenar por fecha
    if orden == 'asc':
        estatus = estatus.order_by('fecha')
    elif orden == 'desc':
        estatus = estatus.order_by('-fecha')

    # Exportar a Excel
    if 'exportar' in request.GET:
        df = pd.DataFrame(list(estatus.values()))
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=estatus_filtrados.xlsx'
        df.to_excel(response, index=False)
        return response

    return render(request, 'estatus/lista_estatus.html', {
        'estatus': estatus,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'orden': orden
    })


# 🟩 Crear un nuevo estatus mediante formulario
def crear_estatus(request):
    if request.method == 'POST':
        form = EstatusSemanalForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_estatus')
    else:
        form = EstatusSemanalForm()
    
    return render(request, 'estatus/crear_estatus.html', {'form': form})
