# Arquivo: apps/usuarios/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URLs de autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('financas/', views.financas_view, name='financas_candidato'),
    path('financas/', views.financas_view, name='financas_candidato'),
    path('cadastro/candidato/', views.cadastrar_candidato, name='cadastro_candidato'),
    path('cadastro/recrutador/', views.cadastrar_recrutador, name='cadastro_recrutador'),
    path('perfil/<str:username>/', views.perfil_publico, name='perfil_publico'),
    path('explorar/', views.explorar_vagas, name='explorar_vagas'),
    path('empresa/<int:empresa_id>/', views.ver_empresa, name='ver_empresa'),
    path('deletar-conta/', views.deletar_conta, name='deletar_conta'),
    

    # NOVAS URLs DE RECUPERAÇÃO DE SENHA
    path('recuperar-senha/', views.recuperar_senha_view, name='recuperar_senha'),
    path('nova-senha/', views.nova_senha_view, name='nova_senha'),
    
    # --- URLs de AJAX ---
    path('ajax/salvar-resumo/', views.ajax_salvar_resumo, name='ajax_salvar_resumo'),
    path('ajax/salvar-experiencia/', views.ajax_salvar_experiencia, name='ajax_salvar_experiencia'),
    path('ajax/salvar-formacao/', views.ajax_salvar_formacao, name='ajax_salvar_formacao'),
    path('ajax/salvar-skill/', views.ajax_salvar_skill, name='ajax_salvar_skill'),
    path('ajax/salvar-curriculo/', views.ajax_salvar_curriculo, name='ajax_salvar_curriculo'),
    path('ajax/deletar-skill/<int:skill_id>/', views.ajax_deletar_skill, name='ajax_deletar_skill'),
    path('ajax/deletar-experiencia/<int:xp_id>/', views.ajax_deletar_experiencia, name='ajax_deletar_experiencia'),
    path('ajax/deletar-formacao/<int:edu_id>/', views.ajax_deletar_formacao, name='ajax_deletar_formacao'),

    # --- URLs DA API (DRF/JWT) ---
    path('api/resumo/', views.ResumoProfissionalAPIView.as_view(), name='api_salvar_resumo'), 
    path('api/experiencia/', views.ExperienciaProfissionalAPIView.as_view(), name='api_salvar_experiencia'),
    path('api/formacao/', views.FormacaoAPIView.as_view(), name='api_salvar_formacao'),
    path('api/skill/', views.SkillAPIView.as_view(), name='api_salvar_skill'),
    path('api/curriculo/', views.CurriculoAPIView.as_view(), name='api_salvar_curriculo'),

]