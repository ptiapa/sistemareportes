from django.contrib import admin
from .models import Proyecto, FlujoCaja

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'estado', 'ppto_total')  # Puedes ajustar los campos

@admin.register(FlujoCaja)
class FlujoCajaAdmin(admin.ModelAdmin):
    list_display = ('proyecto', 'tipo', 'anio', 'total')
