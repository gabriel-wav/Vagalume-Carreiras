# Arquivo: apps/usuarios/urls.py

from django.urls import path
from . import views  # Importa as views do app (views.py)

urlpatterns = [
    # URL para a página de login
    path('login/', views.login_view, name='login'),

    # URL para o processo de logout
    path('logout/', views.logout_view, name='logout'),

    # URL para a página de cadastro de candidato
    path('cadastro/candidato/', views.cadastrar_candidato, name='cadastro_candidato'),

    # URLs de placeholder para os painéis
    path('onboarding/bem-vindo/', views.onboarding_bem_vindo, name='onboarding_bem_vindo'),
    path('onboarding/resumo/', views.onboarding_resumo, name='onboarding_resumo'),
    path('onboarding/salvar-resumo/', views.salvar_resumo, name='salvar_resumo'),

]