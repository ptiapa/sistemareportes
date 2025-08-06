from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_estatus, name='lista_estatus'),
    path('nuevo/', views.crear_estatus, name='crear_estatus'),
]
