# importar_proyectos.py
from decimal import Decimal, InvalidOperation
import pandas as pd
from proyectos.models import Proyecto

# --- util robusto ---
def p(val):
    """
    Convierte valores tipo '1.234.567,89' o '1234567.89' o floats a Decimal(2).
    Vacíos o inválidos -> Decimal('0').
    """
    if val is None:
        return Decimal('0')
    s = str(val).strip()
    if s == '' or s.lower() == 'nan':
        return Decimal('0')

    # si viene como float, conviértelo a string con formato fijo
    # para evitar binarios raros
    try:
        if isinstance(val, float):
            s = f"{val:.10f}"
    except Exception:
        pass

    # normaliza: si hay coma y punto, asumimos formato es-ES ('.' miles, ',' decimal)
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    else:
        # sólo comas -> usa como decimal
        if ',' in s:
            s = s.replace(',', '.')
        # sólo puntos -> lo dejamos tal cual

    # elimina cualquier separador raro de miles (espacios, NBSP)
    s = s.replace('\xa0', '').replace(' ', '')

    try:
        return Decimal(s).quantize(Decimal('0.01'))
    except InvalidOperation:
        return Decimal('0')

# ⚠️ Si NO quieres borrar todo en cada carga, comenta la siguiente línea
# Proyecto.objects.all().delete()

archivo = 'media/CargaP1.xlsm'
# Fuerza columnas numéricas como string para control total
cols_num = [
    "PPTO TOTAL", "Presupuestado GAF 2025",
    "IDENTIFICADO 2025", "Proyectado P6 2025",
    "EJECUTADO 2025"
]
dtype_map = {c: "string" for c in cols_num}
df = pd.read_excel(archivo, sheet_name="CUMPLIMIENTO", dtype=dtype_map)
df.columns = [str(col).strip() for col in df.columns]
df = df.fillna('')

importados = 0
for _, f in df.iterrows():
    codigo = str(f.get("Código", "")).strip()
    if not codigo or codigo.lower() == 'nan':
        continue

    Proyecto.objects.update_or_create(
        codigo=codigo,
        defaults={
            'numero': f.get("N°") if str(f.get("N°")).strip().isdigit() else None,
            'tipo_epi_api': str(f.get("EPI/API", "")).strip(),
            'area': str(f.get("AREA", "")).strip(),
            'nombre': str(f.get("Nombre Proyecto", "")).strip(),
            'estado': str(f.get("ESTADO", "")).strip() or "Pendiente",

            'ppto_total':         p(f.get("PPTO TOTAL")),
            'ppto_gaf_2025':      p(f.get("Presupuestado GAF 2025")),
            'identificado_2025':  p(f.get("IDENTIFICADO 2025")),
            'proyectado_p6_2025': p(f.get("Proyectado P6 2025")),
            'ejecutado':          p(f.get("EJECUTADO 2025")),
        }
    )
    importados += 1

print(f"✅ Proyectos importados/actualizados: {importados}")
