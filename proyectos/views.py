from django.shortcuts import render, get_object_or_404, redirect
from .models import Proyecto, FlujoCaja
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import JsonResponse

from .forms import FlujoCajaForm, ExcelUploadForm, EditarCodigoForm  

import pandas as pd

from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction
from django.urls import reverse

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


# ===== Helpers =====
MAPEO_COLUMNAS = {
    "codigo": "codigo", "código": "codigo", "codigoproyecto": "codigo",
    "código proyecto": "codigo", "cod.proyecto": "codigo",
    "nombre": "nombre", "proyecto": "nombre",
    "estado": "estado", "estatus": "estado",
    "ppto total": "ppto_total", "ppto_total": "ppto_total", "presupuesto total": "ppto_total",
    "ppto gaf 2025": "ppto_gaf_2025", "presupuesto gaf 2025": "ppto_gaf_2025", "gaf 2025": "ppto_gaf_2025",
    "identificado 2025": "identificado_2025", "identificado_2025": "identificado_2025",
    "ejecutado": "ejecutado",
}
CAMPOS_ACTUALIZABLES = {"codigo","nombre","estado","ppto_total","ppto_gaf_2025","identificado_2025","ejecutado"}

def _normaliza_nombre(col: str) -> str:
    return (col or "").strip().lower()

def _to_decimal(val):
    if val is None or (isinstance(val, float) and pd.isna(val)) or (isinstance(val, str) and not val.strip()):
        return None
    try:
        if isinstance(val, str):
            val = val.replace(" ", "").replace(".", "").replace(",", ".")
        return Decimal(str(val))
    except (InvalidOperation, ValueError):
        return None

# ===== Vista: importar Excel =====
@require_http_methods(["GET","POST"])
def importar_proyectos(request):
    if request.method == "GET":
        return render(request, "proyectos/importar.html", {"form": ExcelUploadForm()})

    form = ExcelUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return render(request, "proyectos/importar.html", {"form": form})

    archivo = request.FILES["archivo"]
    hoja = form.cleaned_data.get("hoja") or None

    try:
        df = pd.read_excel(io.BytesIO(archivo.read()), sheet_name=hoja)
    except Exception as e:
        messages.error(request, f"Error leyendo Excel: {e}")
        return render(request, "proyectos/importar.html", {"form": form})

    if df.empty:
        messages.error(request, "El Excel está vacío.")
        return render(request, "proyectos/importar.html", {"form": form})

    # Normaliza encabezados
    df.columns = [_normaliza_nombre(c) for c in df.columns]
    df = df.rename(columns={c: MAPEO_COLUMNAS[c] for c in df.columns if c in MAPEO_COLUMNAS})

    if "codigo" not in df.columns:
        messages.error(request, "No se encontró columna clave 'codigo'.")
        return render(request, "proyectos/importar.html", {"form": form})

    # Filtra solo campos actualizables
    df = df[[c for c in df.columns if c in CAMPOS_ACTUALIZABLES]].copy()

    # Conversión numérica
    for col in ("ppto_total","ppto_gaf_2025","identificado_2025","ejecutado"):
        if col in df.columns:
            df[col] = df[col].apply(_to_decimal)

    # Normaliza código
    df = df[df["codigo"].notna()]
    df["codigo"] = df["codigo"].astype(str).str.strip()
    df = df[df["codigo"]!=""]

    creados, actualizados = 0,0
    with transaction.atomic():
        for _, row in df.iterrows():
            data = {c: row[c] for c in CAMPOS_ACTUALIZABLES if c in row and c!="codigo" and pd.notna(row[c])}
            obj, created = Proyecto.objects.update_or_create(
                codigo=row["codigo"], defaults=data
            )
            if created: creados+=1
            else: actualizados+=1

    messages.success(request, f"Importación: {creados} creados, {actualizados} actualizados.")
    return redirect(reverse("proyectos_lista"))

# ===== Vista: editar código manual =====
def editar_proyecto_codigo(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, id=proyecto_id)

    if request.method == "POST":
        form = EditarCodigoForm(request.POST, initial={"codigo_actual": proyecto.codigo})
        if form.is_valid():
            nuevo = form.cleaned_data["nuevo_codigo"]
            proyecto.codigo = nuevo
            proyecto.save()
            messages.success(request, f"Código actualizado a {nuevo}")
            return redirect(reverse("proyectos_lista"))
    else:
        form = EditarCodigoForm(initial={"codigo_actual": proyecto.codigo})

    return render(request,"proyectos/editar_codigo.html",{"form":form,"proyecto":proyecto})


