from django.shortcuts import render, get_object_or_404, redirect
from .models import Proyecto, FlujoCaja
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import JsonResponse

from .forms import FlujoCajaForm, ExcelUploadForm, EditarCodigoForm, ImportarExcelForm  

import pandas as pd
import io
from decimal import Decimal, InvalidOperation

from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.urls import reverse

import traceback
from unicodedata import normalize

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
    "ficha": "numero",
    "codigo": "codigo",
    "codigo proyecto": "codigo",
    "nombre proyecto": "nombre",
    "nombre": "nombre",
    "gerencia": "area",
    "unidad operativa": None,           # (no existe en el modelo, se ignora)
    "tipo": "tipo_epi_api",
    "estado": "estado",

    "presupuesto total": "ppto_total",
    "ejecutado total": "ejecutado",     # si no quieres pisar, comenta esta línea

    "comprometido total": None,         # (no existe en el modelo)
    "presupuesto ano": "ppto_gaf_2025",
    "identificado ano": "identificado_2025",
    "ejecutado ano": "ejecutado",       # YTD

    "fisico total": None,
    "financiero total": None,
    "fisico ano": None,
    "financiero ano": None,
    "avance fisico": None,
}

NUMERIC_FIELDS = {"ppto_total", "ppto_gaf_2025", "identificado_2025", "ejecutado"}
TEXT_FIELDS    = {"nombre", "estado", "tipo_epi_api", "area"}

def _norm(s: str) -> str:
    s = (str(s) if s is not None else "").strip().lower()
    s = s.replace("<br>", " ").replace("\n", " ")
    # quita acentos: año -> ano, código -> codigo, etc.
    s = normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    # colapsa espacios
    return " ".join(s.split())
    return (col or "").strip().lower()

def _to_decimal(val):
    """Convierte '1.234.567,89' o '1,234,567.89' a Decimal; None si vacío."""
    if val is None or (isinstance(val, float) and pd.isna(val)) or (isinstance(val, str) and val.strip() == ""):
        return None
    s = str(val).strip().replace(" ", "")
    if s.count(",") == 1 and s.count(".") > 1:
        s = s.replace(".", "").replace(",", ".")
    elif s.count(",") > 1 and s.count(".") == 1:
        s = s.replace(",", "")
    elif s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None

def _to_int(val):
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)) or (isinstance(val, str) and val.strip() == ""):
            return None
        return int(str(val).strip())
    except Exception:
        return None

# ===== Vista: importar Excel =====
@require_http_methods(["GET", "POST"])
def importar_proyectos(request):
    if request.method == "GET":
        return render(request, "proyectos/importar.html", {"form": ExcelUploadForm()})

    form = ExcelUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, f"Formulario inválido: {form.errors}")
        return render(request, "proyectos/importar.html", {"form": form})

    archivo = form.cleaned_data["archivo"]
    hoja = form.cleaned_data.get("hoja") or 0

    # 1) Leer Excel
    import io, traceback
    try:
        buffer = archivo.read()
        df = pd.read_excel(io.BytesIO(buffer), sheet_name=hoja, engine="openpyxl")
    except Exception as e:
        traceback.print_exc()
        messages.error(request, f"Error leyendo el Excel: {e}")
        return render(request, "proyectos/importar.html", {"form": ExcelUploadForm()})

    if df is None or df.empty:
        messages.warning(request, "El Excel no tiene filas.")
        return render(request, "proyectos/importar.html", {"form": ExcelUploadForm()})

    # 2) Normalizar/renombrar encabezados
    norm_cols = [_norm(c) for c in df.columns]
    df.columns = norm_cols
    rename_map = {}
    for c in norm_cols:
        destino = MAPEO_COLUMNAS.get(c)
        if destino:
            rename_map[c] = destino
    df = df.rename(columns=rename_map)

    # 3) Chequeos mínimos
    if "codigo" not in df.columns:
        messages.error(
            request,
            "No se encontró la columna de código. Usa 'Código' o 'Codigo'."
        )
        return render(request, "proyectos/importar.html", {"form": ExcelUploadForm()})

    # 4) Crear columnas vacías si faltan
    for col in (TEXT_FIELDS | NUMERIC_FIELDS | {"numero"}):
        if col not in df.columns:
            df[col] = None

    # 5) Conversiones
    for col in NUMERIC_FIELDS:
        df[col] = df[col].apply(_to_decimal)
    if "numero" in df.columns:
        df["numero"] = df["numero"].apply(_to_int)

    # 6) Limpiar códigos
    df["codigo"] = df["codigo"].astype(str).str.strip()
    df = df[df["codigo"] != ""]
    if df.empty:
        messages.warning(request, "No se encontraron filas con `Código` válido.")
        return render(request, "proyectos/importar.html", {"form": ExcelUploadForm()})

    # 7) Guardar
    creados = 0
    actualizados = 0
    try:
        with transaction.atomic():
            for _, row in df.iterrows():
                codigo = row["codigo"]
                defaults = {}

                for t in TEXT_FIELDS:
                    val = row.get(t)
                    if val is not None and str(val).strip() != "":
                        defaults[t] = str(val).strip()

                for n in NUMERIC_FIELDS:
                    defaults[n] = row.get(n)

                if row.get("numero") is not None:
                    defaults["numero"] = row["numero"]

                obj, created = Proyecto.objects.update_or_create(
                    codigo=codigo,
                    defaults=defaults
                )
                if created:
                    creados += 1
                else:
                    actualizados += 1

    except IntegrityError as e:
        messages.error(request, f"Error de integridad al guardar: {e}")
        return render(request, "proyectos/importar.html", {"form": ExcelUploadForm()})
    except Exception as e:
        messages.error(request, f"Ocurrió un error al guardar: {e}")
        return render(request, "proyectos/importar.html", {"form": ExcelUploadForm()})

    messages.success(request, f"Importación OK: {creados} creados, {actualizados} actualizados.")
    return redirect("proyectos_lista")

@require_http_methods(["GET", "POST"])
def editar_proyecto_codigo(request, pk):
    proyecto = get_object_or_404(Proyecto, pk=pk)

    if request.method == "POST":
        form = EditarCodigoForm(request.POST, proyecto=proyecto)
        if form.is_valid():
            nuevo = form.cleaned_data["nuevo_codigo"].strip()
            if nuevo != proyecto.codigo:
                proyecto.codigo = nuevo
                proyecto.save(update_fields=["codigo"])
                messages.success(request, "✅ Código actualizado.")
            else:
                messages.info(request, "No hubo cambios.")
            return redirect("proyectos_lista")
        else:
            messages.error(request, "Revisa el formulario.")
    else:
        form = EditarCodigoForm(
            proyecto=proyecto,
            initial={"codigo_actual": proyecto.codigo, "nuevo_codigo": proyecto.codigo},
        )

    return render(
        request,
        "proyectos/editar_codigo.html",
        {"form": form, "proyecto": proyecto},
    )



