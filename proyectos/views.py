from django.shortcuts import render, get_object_or_404, redirect
from .models import Proyecto, FlujoCaja
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.http import JsonResponse

from .forms import FlujoCajaForm, ExcelUploadForm, EditarCodigoForm, ImportarExcelForm  

import pandas as pd
import io
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, getcontext

from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.urls import reverse

import traceback
from unicodedata import normalize

import numbers
import re

from decimal import Decimal, InvalidOperation


TWOCENTS = Decimal("0.01")
BILLION = Decimal("1000000000")

getcontext().prec = 28  # precisión suficiente


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

def parse_money(val):
    """
    Convierte strings/float/int a Decimal sin perder el punto decimal.
    - Acepta formatos ES ('.' miles, ',' decimal) y EN ('.' decimal).
    - NO elimina el punto si es el separador decimal real.
    """
    if val is None:
        return None

    # Tipos numéricos nativos
    if isinstance(val, Decimal):
        return val
    if isinstance(val, int):
        return Decimal(val)
    if isinstance(val, float):
        # Nunca Decimal(val) directo por el binario -> usa str()
        return Decimal(str(val))

    # Strings
    s = str(val).strip().replace('\u00A0', '').replace(' ', '')  # limpia espacios/nbsp
    # Si hay punto y coma, asumimos ES -> '.' miles y ',' decimal
    if '.' in s and ',' in s:
        s = s.replace('.', '').replace(',', '.')
    else:
        # Si solo hay coma, trátala como decimal
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')

    # Deja solo dígitos, un signo inicial opcional y el punto decimal
    s = re.sub(r'(?<!^)-|[^0-9\.-]', '', s)

    try:
        return Decimal(s)
    except InvalidOperation:
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
    """
    Importa un Excel y ACTUALIZA proyectos existentes por 'codigo'.
    NO crea nuevos. Ignora filas sin código y columnas que no existan.
    """
    if request.method == "GET":
        return render(request, "proyectos/importar.html", {"form": ImportarExcelForm()})

    form = ImportarExcelForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Formulario inválido. Revisa los campos.")
        return render(request, "proyectos/importar.html", {"form": form})

    archivo = form.cleaned_data["archivo"]
    hoja = form.cleaned_data.get("hoja") or 0  # primera hoja si no dan nombre

    try:
        # pandas soporta file-like directamente
        df = pd.read_excel(archivo, sheet_name=hoja)
    except Exception as e:
        messages.error(request, f"No se pudo leer el Excel: {e}")
        return render(request, "proyectos/importar.html", {"form": form})

    if df.empty:
        messages.warning(request, "El Excel no tiene filas para procesar.")
        return render(request, "proyectos/importar.html", {"form": form})

    # Mapeo flexible de encabezados Excel -> campos del modelo
    # Acepta variantes comunes de tus encabezados:
    # "Ficha, Código, Nombre Proyecto, Gerencia, Unidad Operativa, Tipo, Estado,
    #  Presupuesto Total, Ejecutado Total, Comprometido Total, Presupuesto Año,
    #  Identificado Año, Ejecutado Año, Fisico Total, Financiero Total,
    #  Fisico Año, Financiero Año, Avance Fisico"
    col_norm = { _norm(c): c for c in df.columns }

    def find_col(*candidatos):
        for c in candidatos:
            if c in col_norm:
                return col_norm[c]
        return None

    col_codigo   = find_col("codigo", "codigo proyecto", "cod")
    col_nombre   = find_col("nombre proyecto", "nombre")
    col_estado   = find_col("estado")
    col_ppto_tot = find_col("presupuesto total", "ppto total", "presupuesto_total", "ppto_total")
    col_ppto_ano = find_col("presupuesto ano", "presupuesto año", "ppto gaf 2025", "gaf 2025")
    col_ident_25 = find_col("identificado ano", "identificado año", "identificado 2025")
    col_ejec_ano = find_col("ejecutado ano", "ejecutado año", "ejecutado 2025")

    if not col_codigo:
        messages.error(request, "No se encontró la columna de CÓDIGO en el Excel.")
        return render(request, "proyectos/importar.html", {"form": form})

    # Contadores
    total_rows = len(df)
    sin_codigo = 0
    no_encontrado = 0
    actualizados = 0
    sin_cambios  = 0
    errores      = 0

    # Utilidad para convertir a Decimal seguro
    def to_decimal(val):
        if pd.isna(val):
            return None
        try:
            # Maneja valores con coma o punto
            s = str(val).replace(".", "").replace(",", ".")
            # si quedó solo punto, limpia:
            if s == ".":
                return None
            return Decimal(s)
        except Exception:
            return None

    @transaction.atomic
    def _procesar():
        nonlocal sin_codigo, no_encontrado, actualizados, sin_cambios, errores

        for idx, row in df.iterrows():
            # 1) Código (clave)
            raw_code = row.get(col_codigo)
            code = ("" if pd.isna(raw_code) else str(raw_code)).strip()
            if not code:
                sin_codigo += 1
                continue

            try:
                proyecto = Proyecto.objects.get(codigo=code)
            except Proyecto.DoesNotExist:
                no_encontrado += 1
                continue
            except Exception:
                errores += 1
                continue

            cambios = 0

            # 2) nombre (texto)
            if col_nombre:
                raw = row.get(col_nombre)
                if not pd.isna(raw):
                    nuevo = str(raw).strip()
                    if nuevo and nuevo != proyecto.nombre:
                        proyecto.nombre = nuevo
                        cambios += 1

            # 3) estado (texto)
            if col_estado:
                raw = row.get(col_estado)
                if not pd.isna(raw):
                    nuevo = str(raw).strip()
                    if nuevo and nuevo != proyecto.estado:
                        proyecto.estado = nuevo
                        cambios += 1

            # 4) ppto_total (decimal)
            if col_ppto_tot:
                nuevo = to_decimal(row.get(col_ppto_tot))
                if nuevo is not None and nuevo != proyecto.ppto_total:
                    proyecto.ppto_total = nuevo
                    cambios += 1

            # 5) ppto_gaf_2025 (desde "Presupuesto Año")
            if col_ppto_ano:
                nuevo = to_decimal(row.get(col_ppto_ano))
                if nuevo is not None and nuevo != proyecto.ppto_gaf_2025:
                    proyecto.ppto_gaf_2025 = nuevo
                    cambios += 1

            # 6) identificado_2025 (decimal)
            if col_ident_25:
                nuevo = to_decimal(row.get(col_ident_25))
                if nuevo is not None and nuevo != proyecto.identificado_2025:
                    proyecto.identificado_2025 = nuevo
                    cambios += 1

            # 7) ejecutado (usamos "Ejecutado Año")
            if col_ejec_ano:
                nuevo = to_decimal(row.get(col_ejec_ano))
                if nuevo is not None and nuevo != proyecto.ejecutado:
                    proyecto.ejecutado = nuevo
                    cambios += 1

            if cambios:
                try:
                    proyecto.save()
                    actualizados += 1
                except Exception:
                    errores += 1
            else:
                sin_cambios += 1

    # Ejecuta el procesamiento dentro de una transacción
    try:
        _procesar()
    except Exception as e:
        messages.error(request, f"Ocurrió un error al procesar: {e}")
        return render(request, "proyectos/importar.html", {"form": form})

    # Resumen para el usuario
    messages.success(
        request,
        (
            f"Procesadas {total_rows} filas. "
            f"Actualizados: {actualizados}. "
            f"Sin cambios: {sin_cambios}. "
            f"Sin código: {sin_codigo}. "
            f"No encontrados: {no_encontrado}. "
            f"Errores: {errores}."
        )
    )

    # Nota de columnas detectadas (informativa)
    cols_info = []
    for label, col in [
        ("Código", col_codigo),
        ("Nombre", col_nombre),
        ("Estado", col_estado),
        ("Ppto Total", col_ppto_tot),
        ("Presupuesto Año → GAF 2025", col_ppto_ano),
        ("Identificado Año → Identificado_2025", col_ident_25),
        ("Ejecutado Año → Ejecutado", col_ejec_ano),
    ]:
        cols_info.append(f"{label}: {'OK' if col else '—'}")

    messages.info(request, "Columnas reconocidas → " + " | ".join(cols_info))

    return render(request, "proyectos/importar.html", {"form": ImportarExcelForm()})

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



