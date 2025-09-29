from django.contrib import admin
from .models import Proyecto, FlujoCaja

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
   # El primero NO puede ser editable, por eso pongo 'id' primero
    list_display = (
        'id','numero','codigo','tipo_epi_api','area','nombre','estado',
        'ppto_total','ppto_gaf_2025','identificado_2025','proyectado_p6_2025','ejecutado'
    )
    list_filter = ('estado','area','tipo_epi_api')
    search_fields = ('codigo','nombre')
    list_editable = (
        'numero','codigo','estado','ppto_total','ppto_gaf_2025',
        'identificado_2025','proyectado_p6_2025','ejecutado'
    )
    ordering = ('numero','codigo')

@admin.register(FlujoCaja)
class FlujoCajaAdmin(admin.ModelAdmin):
    list_display = (
        'proyecto','tipo','anio','enero','febrero','marzo','abril','mayo','junio',
        'julio','agosto','septiembre','octubre','noviembre','diciembre'
    )
    list_filter = ('tipo','anio')
    search_fields = ('proyecto__codigo','proyecto__nombre')
