import pandas as pd
from estatus.models import EstatusSemanal

EstatusSemanal.objects.all().delete()
print("🔁 Todos los estatus anteriores fueron eliminados.\n")

archivo = 'media/CargaP1.xlsm'
df = pd.read_excel(archivo, sheet_name="Informe Semanal")
df.columns = [col.strip() for col in df.columns]
df = df.fillna('')

def get_val(fila, col):
    val = fila.get(col, '')
    return str(val).strip().replace('\xa0', '') if val else ''

importados = 0
for _, fila in df.iterrows():
    try:
        if not get_val(fila, "CÓDIGOPROYECTO"):
            continue

        fecha = pd.to_datetime(fila.get("FECHA"), errors='coerce')
        if pd.isna(fecha):
            continue

        EstatusSemanal.objects.create(
            prioridad=int(get_val(fila, "PRI")) if get_val(fila, "PRI").isdigit() else None,
            codigo_proyecto=get_val(fila, "CÓDIGOPROYECTO"),
            jefe_proyecto=get_val(fila, "JEFE DE"),
            eecc=get_val(fila, "EECC"),
            proyecto=get_val(fila, "PROYECTO"),
            servicio=get_val(fila, "SERVICIO"),
            autor=get_val(fila, "PERSONA"),
            fecha=fecha.date(),
            comentario=get_val(fila, "COMENTARIO")
        )
        importados += 1

    except Exception as e:
        print(f"⚠️ Error al cargar estatus: {e}")

print(f"\n✅ Estatus importados: {importados}")
