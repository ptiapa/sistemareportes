from django.urls import path
from .views import lista_proyectos, lista_flujo_caja, editar_flujo, importar_proyectos, editar_proyecto_codigo   

urlpatterns = [
    path('', lista_proyectos, name='lista_proyectos'),
    path('', lista_proyectos, name='proyectos_lista'),
    path('flujo/', lista_flujo_caja, name='lista_flujo_caja'),
    path("flujo/<int:pk>/", editar_flujo, name="editar_flujo"),  
    path("importar/", importar_proyectos, name="proyectos_importar"),
    path("<int:pk>/editar-codigo/", editar_proyecto_codigo, name="editar_proyecto_codigo"),
    
]

