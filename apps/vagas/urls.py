# Arquivo: apps/vagas/urls.py

from django.urls import path
from . import views  # Importa as views do app (views.py)

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('vagas/criar/', views.criar_vaga, name='criar_vaga'),
    path('vagas/editar/<int:vaga_id>/', views.editar_vaga, name='editar_vaga'),
    path('vagas/deletar/<int:vaga_id>/', views.deletar_vaga, name='deletar_vaga'),
    path('vagas/aplicar/<int:vaga_id>/', views.aplicar_vaga, name='aplicar_vaga'),
    path('dashboard/candidato/', views.home_candidato, name='home_candidato'),
    path('dashboard/recrutador/', views.home_recrutador, name='home_recrutador'),
    path('vagas/<int:vaga_id>/candidatos/', views.ver_candidatos_vaga, name='ver_candidatos_vaga'),
    path('radar-de-talentos/', views.radar_de_talentos, name='radar_de_talentos'),
    path('perfil_empresa/', views.perfil_empresa, name='perfil_empresa'),
    path("planos_empresa/", views.planos_empresa, name="planos_empresa"),
    path('painel-admin/', views.painel_admin, name='painel_admin'),
    path('politica-de-privacidade/', views.politica_privacidade, name='politica_de_privacidade'),
]