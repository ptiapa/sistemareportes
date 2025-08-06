from django.urls import path
from .views import lista_proyectos, lista_flujo_caja, editar_flujo  

urlpatterns = [
    path('', lista_proyectos, name='lista_proyectos'),
    path('flujo/', lista_flujo_caja, name='lista_flujo_caja'),
    path('flujo/editar/<int:flujo_id>/', editar_flujo, name='editar_flujo'),  
    
]
