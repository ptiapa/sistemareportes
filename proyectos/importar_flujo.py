import pandas as pd
from proyectos.models import FlujoCaja, Proyecto

# 🧹 Eliminar datos anteriores
FlujoCaja.objects.all().delete()
print("🧹 Datos anteriores de flujo eliminados.\n")

# 📥 Cargar Excel
archivo = 'media/FLUJO DE CAJA PROYECTOS.xlsx'
df = pd.read_excel(archivo)
df = df.fillna('')  # Reemplaza NaN por string vacío

# 🔧 Función para convertir a decimal seguro
def get_decimal(val):
    try:
        return float(val) if str(val).strip() not in ['', '-', 'nan'] else 0
    except:
        return 0

# 🔁 Recorrer filas
registros = 0
errores = 0

for _, fila in df.iterrows():
    codigo = str(fila.get("Código")).strip()
    tipo = str(fila.get("Tipo")).strip()

    if not codigo or not tipo:
        continue

    if tipo not in ['PROG.', 'PROG.P6', 'REAL']:
        print(f"⚠️ Tipo no válido '{tipo}' en proyecto {codigo}")
        continue

    try:
        proyecto = Proyecto.objects.get(codigo=codigo)
    except Proyecto.DoesNotExist:
        print(f"⚠️ Proyecto no encontrado: {codigo}")
        continue

    try:
        FlujoCaja.objects.create(
            proyecto=proyecto,
            tipo=tipo,
            enero=get_decimal(fila.get("Enero")),
            febrero=get_decimal(fila.get("Febrero")),
            marzo=get_decimal(fila.get("Marzo")),
            abril=get_decimal(fila.get("Abril")),
            mayo=get_decimal(fila.get("Mayo")),
            junio=get_decimal(fila.get("Junio")),
            julio=get_decimal(fila.get("Julio")),
            agosto=get_decimal(fila.get("Agosto")),
            septiembre=get_decimal(fila.get("Septiembre")),
            octubre=get_decimal(fila.get("Octubre")),
            noviembre=get_decimal(fila.get("Noviembre")),
            diciembre=get_decimal(fila.get("Diciembre")),
        )
        registros += 1
    except Exception as e:
        errores += 1
        print(f"⚠️ Error al importar {codigo} - {e}")

print(f"\n✅ Importación completa. Registros cargados: {registros}, errores: {errores}")
