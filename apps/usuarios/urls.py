# Arquivo: apps/usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URLs de autenticação (permanecem iguais)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('financas/', views.financas_view, name='financas_candidato'),
    path('cadastro/candidato/', views.cadastrar_candidato, name='cadastro_candidato'),
    path('cadastro/recrutador/', views.cadastrar_recrutador, name='cadastro_recrutador'),

    # ATENÇÃO: Removemos as URLs de /onboarding/ aqui
    
    # --- URLs de AJAX ---
    path('ajax/salvar-resumo/', views.ajax_salvar_resumo, name='ajax_salvar_resumo'),
    path('ajax/salvar-experiencia/', views.ajax_salvar_experiencia, name='ajax_salvar_experiencia'),
    path('ajax/salvar-formacao/', views.ajax_salvar_formacao, name='ajax_salvar_formacao'),
    path('ajax/salvar-skill/', views.ajax_salvar_skill, name='ajax_salvar_skill'),
    path('ajax/salvar-curriculo/', views.ajax_salvar_curriculo, name='ajax_salvar_curriculo'),

    # --- URLs DA API (DRF/JWT) ---
    path('api/resumo/', views.ResumoProfissionalAPIView.as_view(), name='api_salvar_resumo'), 
    path('api/experiencia/', views.ExperienciaProfissionalAPIView.as_view(), name='api_salvar_experiencia'),
    path('api/formacao/', views.FormacaoAPIView.as_view(), name='api_salvar_formacao'),
    path('api/skill/', views.SkillAPIView.as_view(), name='api_salvar_skill'),
    path('api/curriculo/', views.CurriculoAPIView.as_view(), name='api_salvar_curriculo'),
]