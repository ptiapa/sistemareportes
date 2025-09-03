from django.contrib import admin
from .models import Proyecto, FlujoCaja

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    # Lo que se ve en la tabla de lista
    list_display = (
        "codigo", "nombre", "numero", "estado",
        "ppto_total", "ppto_gaf_2025", "identificado_2025", "ejecutado",
    )
    # Enlaces clicables (no deben incluir campos que estén en list_editable)
    list_display_links = ("codigo", "nombre")
    # Para buscar rápido
    search_fields = ("codigo", "nombre")
    # Filtros laterales útiles
    list_filter = ("estado", "area", "tipo_epi_api")
    # Editar directamente desde la lista (opcional)
    list_editable = ("numero",)  # podrás cambiar 'numero' en la tabla y dar "Save"

@admin.register(FlujoCaja)
class FlujoCajaAdmin(admin.ModelAdmin):
    list_display = ("proyecto", "tipo", "anio", "enero", "febrero", "marzo", "abril",
                    "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
                    "noviembre", "diciembre")
    list_filter = ("tipo", "anio", "proyecto")
    search_fields = ("proyecto__codigo", "proyecto__nombre")
