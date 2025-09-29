# proyectos/management/commands/importar_proyectos.py
from decimal import Decimal, InvalidOperation
import re
import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from proyectos.models import Proyecto

# ---------- helpers ----------

def _canon(s: str) -> str:
    """Normaliza encabezados (quita espacios, NBSP y lowercase)."""
    return str(s or "").replace("\u00A0", " ").strip().lower()

# sinónimos tolerantes para los encabezados que esperamos
HEADERS = {
    "nro": {"n°", "no", "nº", "nro", "numero", "número"},
    "codigo": {"codigo", "código", "cod"},
    "epi_api": {"epi/api", "epi", "api", "epi / api"},
    "area": {"area", "área"},
    "nombre": {"nombre del proyecto", "nombre proyecto", "nombre"},
    "estado": {"estado", "estatus"},
    "ppto_total": {"ppto total", "pp to tal", "ppto", "ppto_total"},
    "gaf_2025": {"presupuestado gaf 2025", "gaf 2025", "presup_gaf_2025"},
    "identificado_2025": {"identificado 2025", "identificado_2025"},
    "proyectado_p6_2025": {"proyectado p6 2025", "proyectado p6", "proyectado_p6_2025"},
    "ejecutado": {"ejecutado 2025", "ejecutado", "ejecutado_año"},
}

def map_headers(df_cols):
    """Devuelve un dict {clave_interna: nombre_real_en_df} o lanza error si falta alguno vital."""
    cols_norm = { _canon(c): c for c in df_cols }
    out = {}
    required = ["codigo", "nombre", "estado",
                "ppto_total", "gaf_2025", "identificado_2025",
                "proyectado_p6_2025", "ejecutado"]

    # opcionales
    for key, variants in HEADERS.items():
        for v in variants:
            if v in cols_norm:
                out[key] = cols_norm[v]
                break

    missing = [k for k in required if k not in out]
    if missing:
        raise CommandError(f"Faltan columnas en el Excel: {missing}\n"
                           f"Encabezados detectados: {list(df_cols)}")
    return out

def parse_money(val) -> Decimal:
    """
    Convierte valores tipo "1.234.567,89", "1234567.89", "1 234 567,89" o float a Decimal(2).
    Vacíos/invalid -> Decimal('0.00').
    """
    if val is None:
        return Decimal("0.00")

    # evita floats binarios raros: primero a string
    s = str(val).strip()
    if s == "" or s.lower() == "nan":
        return Decimal("0.00")

    # normaliza separadores es-ES: si hay . y , asumimos '.' miles y ',' decimales
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")

    # elimina espacios y NBSP
    s = s.replace("\u00A0", "").replace(" ", "")

    # permite solo números, punto y signo inicial
    s = re.sub(r"(?<!^)-|[^0-9\.-]", "", s)

    try:
        return Decimal(s).quantize(Decimal("0.01"))
    except InvalidOperation:
        return Decimal("0.00")


# ---------- command ----------

class Command(BaseCommand):
    help = "Importa/actualiza proyectos desde un Excel, parseando decimales correctamente."

    def add_arguments(self, parser):
        parser.add_argument(
            "--archivo",
            default="media/Grilla.xlsx",
            help="Ruta al .xlsx/.xlsm (por defecto: media/Grilla.xlsx)",
        )
        parser.add_argument(
            "--hoja",
            default="CUMPLIMIENTO",
            help='Nombre de la hoja (por defecto: "CUMPLIMIENTO")',
        )
        parser.add_argument(
            "--borrar",
            action="store_true",
            help="Borra todos los proyectos antes de importar.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No guarda, solo muestra cuántos importaría.",
        )

    def handle(self, *args, **opts):
        archivo = opts["archivo"]
        hoja = opts["hoja"]
        dry = opts["dry_run"]

        # leemos TODO como string para controlar completamente el parseo
        try:
            df = pd.read_excel(archivo, sheet_name=hoja, dtype="string")
        except Exception as e:
            raise CommandError(f"Error leyendo '{archivo}' hoja '{hoja}': {e}")

        # normaliza encabezados
        df.columns = [str(c).strip() for c in df.columns]
        header_map = map_headers(df.columns)

        # borrar si corresponde
        if opts["borrar"] and not dry:
            Proyecto.objects.all().delete()
            self.stdout.write(self.style.WARNING("⚠️  Se borraron todos los proyectos."))

        # completa vacíos
        df = df.fillna("")

        ok, nuevos, actualizados = 0, 0, 0
        for _, row in df.iterrows():
            codigo = str(row.get(header_map["codigo"], "")).strip()
            if not codigo or codigo.lower() == "nan":
                continue

            defaults = {
                "numero": None,  # si en tu Excel tienes el N°, puedes mapearlo igual que el resto
                "tipo_epi_api": str(row.get(HEADERS["epi_api"] & set(df.columns) and header_map.get("epi_api", ""), "")).strip(),
                "area":         str(row.get(HEADERS["area"]    & set(df.columns) and header_map.get("area", ""), "")).strip(),
                "nombre":       str(row.get(header_map["nombre"], "")).strip(),
                "estado":       str(row.get(header_map["estado"], "")).strip() or "Pendiente",

                "ppto_total":         parse_money(row.get(header_map["ppto_total"])),
                "ppto_gaf_2025":      parse_money(row.get(header_map["gaf_2025"])),
                "identificado_2025":  parse_money(row.get(header_map["identificado_2025"])),
                "proyectado_p6_2025": parse_money(row.get(header_map["proyectado_p6_2025"])),
                "ejecutado":          parse_money(row.get(header_map["ejecutado"])),
            }

            if dry:
                ok += 1
                continue

            obj, created = Proyecto.objects.update_or_create(codigo=codigo, defaults=defaults)
            ok += 1
            if created: nuevos += 1
            else:       actualizados += 1

        msg = f"✅ Filas procesadas: {ok}"
        if dry:
            self.stdout.write(self.style.SUCCESS(msg + " (DRY-RUN, no se guardó nada)"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"{msg}. Nuevos: {nuevos} • Actualizados: {actualizados}"
            ))
