import pandas as pd
from proyectos.models import Proyecto

# ⚠️ Eliminar todos los proyectos antes de importar
Proyecto.objects.all().delete()
print("🔁 Todos los proyectos existentes fueron eliminados.\n")

# Leer archivo Excel
archivo = 'media/CargaP1.xlsm'
df = pd.read_excel(archivo, sheet_name="CUMPLIMIENTO")
df.columns = [col.strip() for col in df.columns]
df = df.fillna('')

total = 0
importados = 0

for _, fila in df.iterrows():
    codigo = str(fila.get("Código")).strip()
    if not codigo or codigo.lower() == 'nan':
        continue

    try:
        Proyecto.objects.update_or_create(
            codigo=codigo,
            defaults={
                'numero': fila.get("N°"),
                'tipo_epi_api': fila.get("EPI/API"),
                'area': fila.get("AREA"),
                'nombre': fila.get("Nombre Proyecto"),
                'estado': fila.get("ESTADO") or "Pendiente",
                'ppto_total': fila.get("PPTO TOTAL") or 0,
                'ppto_gaf_2025': fila.get("Presupuestado GAF 2025") or 0,
                'identificado_2025': fila.get("IDENTIFICADO 2025") or 0,
                'proyectado_p6_2025': fila.get("Proyectado P6 2025") or 0,
                'ejecutado': fila.get("EJECUTADO 2025") or 0
            }
        )
        importados += 1
    except Exception as e:
        print(f"⚠️ Error al cargar proyecto {codigo}: {e}")

print(f"\n✅ Proyectos importados: {importados} de {len(df)} filas procesadas.")
