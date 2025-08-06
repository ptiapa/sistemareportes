from django.shortcuts import render, get_object_or_404, redirect
from .models import Proyecto, FlujoCaja
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import JsonResponse

from .forms import FlujoCajaForm  

import pandas as pd

def lista_proyectos(request):
    proyectos = Proyecto.objects.all()
    return render(request, 'proyectos/lista_proyectos.html', {'proyectos': proyectos})

def lista_flujo_caja(request):
    anio = request.GET.get('anio')
    estados_seleccionados = request.GET.getlist('estado')

    proyectos_dict = {}

    flujo = FlujoCaja.objects.select_related('proyecto').order_by('proyecto__codigo', 'tipo')

    if anio:
        flujo = flujo.filter(anio=anio)
    if estados_seleccionados:
        flujo = flujo.filter(proyecto__estado__in=estados_seleccionados)

    for item in flujo:
        codigo = item.proyecto.codigo
        if codigo not in proyectos_dict:
            proyectos_dict[codigo] = {
                'proyecto': item.proyecto,
                'flujos': []
            }
        proyectos_dict[codigo]['flujos'].append(item)

    # Excel export (opcional)
    if 'exportar' in request.GET:
        data = []
        for grupo in proyectos_dict.values():
            for f in grupo['flujos']:
                data.append({
                    'Código': grupo['proyecto'].codigo,
                    'Nombre': grupo['proyecto'].nombre,
                    'Tipo': f.tipo,
                    'Enero': f.enero,
                    'Febrero': f.febrero,
                    'Marzo': f.marzo,
                    'Abril': f.abril,
                    'Mayo': f.mayo,
                    'Junio': f.junio,
                    'Julio': f.julio,
                    'Agosto': f.agosto,
                    'Septiembre': f.septiembre,
                    'Octubre': f.octubre,
                    'Noviembre': f.noviembre,
                    'Diciembre': f.diciembre,
                })
        df = pd.DataFrame(data)
        response = HttpResponse(content_type='application/vnd.ms-excel')
        response['Content-Disposition'] = 'attachment; filename=flujo_caja.xlsx'
        df.to_excel(response, index=False)
        return response

    años_disponibles = FlujoCaja.objects.values_list('anio', flat=True).distinct().order_by('anio')
    estados_disponibles = Proyecto.objects.values_list('estado', flat=True).distinct().order_by('estado')

    return render(request, 'proyectos/lista_flujo_caja.html', {
        'proyectos_flujo': proyectos_dict.values(),
        'años_disponibles': años_disponibles,
        'anio': int(anio) if anio else '',
        'estados_disponibles': estados_disponibles,
        'estados_seleccionados': estados_seleccionados
    })

 
def editar_flujo(request, flujo_id):
    flujo = get_object_or_404(FlujoCaja, id=flujo_id)

    if request.method == 'POST':
        form = FlujoCajaForm(request.POST, instance=flujo)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True})
    else:
        form = FlujoCajaForm(instance=flujo)

    html = render_to_string('proyectos/form_editar_flujo_modal.html', {
        'form': form,
        'flujo': flujo
    }, request=request)

    return JsonResponse({'success': False, 'html': html})

