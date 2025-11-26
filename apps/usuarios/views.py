# Arquivo: apps/usuarios/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from .models import (
    Usuario, Candidato, Resumo_Profissional, 
    Experiencia, Formacao_Academica, Skill,
    Empresa, Recrutador
)
from .forms import (
    CandidatoCadastroForm, ExperienciaForm, 
    FormacaoForm, SkillForm, CurriculoForm,
    RecrutadorCadastroForm
)
from django import forms
import re
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .permissions import IsCandidato
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from apps.usuarios.models import AvaliacaoEmpresa



@transaction.atomic
def cadastrar_candidato(request):
    """
    Processa o formulário de cadastro do UC01.
    """
    if request.method == 'POST':
        form = CandidatoCadastroForm(request.POST)
        
        if form.is_valid():
            # ... (seu código de criação do user e candidato continua igual) ...
            data = form.cleaned_data
            
            user = Usuario.objects.create_user(
                username=data['email'],
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                telefone=data['telefone'],
                tipo_usuario='candidato'
            )
            
            candidato = Candidato.objects.create(
                usuario=user,
                cpf=data['cpf']
            )
            
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.info(request, 'Bem-vindo!', extra_tags='FIRST_LOGIN')
            
            # --- CORREÇÃO IMPORTANTE ---
            # Redireciona para o INÍCIO da "cutscene", não para o final.
            return redirect('home_candidato') 
            # ---------------------------
    
    else:
        form = CandidatoCadastroForm()
        
    return render(request, 'usuarios/cadastro_candidato.html', {'form': form})

def login_view(request):
    """
    Processa a página de login para Candidatos e Recrutadores (UC03).
    """
    if request.method == 'POST':
        login_identifier = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=login_identifier, password=password)

        if user is not None:
            is_first_login = (user.last_login is None)
            login(request, user)

            if user.tipo_usuario == 'candidato':
                # O diff do seu colega removeu a lógica do 'is_first_login' aqui
                # Vamos manter a sua lógica original do 'main'
                if is_first_login:
                    messages.info(request, 'Bem-vindo!', extra_tags='FIRST_LOGIN')
                
                return redirect('home_candidato') # Lógica do 'main' mantida
            
            elif user.tipo_usuario == 'recrutador':
                return redirect('home_recrutador')
            
            return redirect('home_candidato')
        else:
            messages.error(request, 'Credenciais inválidas. Por favor, tente novamente.')
            
    return render(request, 'usuarios/login.html')

def logout_view(request):
    logout(request)
    return redirect('login') # Redireciona para 'login' (do seu 'main')

@login_required # 1. Garante que o usuário está logado (via sessão)
def financas_view(request):
    """
    Renderiza a página de Finanças, protegida para candidatos.
    """
    # 2. Garante que é um candidato (baseado no seu 'tipo_usuario')
    if request.user.tipo_usuario != 'candidato':
        # Se um recrutador tentar acessar, ele é barrado.
        return HttpResponseForbidden("Acesso negado.")

    # Se passou nas verificações, renderiza o template
    context = {
        'pagina_ativa': 'financas' # Para o sub-nav
    }
    return render(request, 'usuarios/financas.html', context)

# ---
# AQUI COMEÇA A "CUTSCENE" DE ONBOARDING
# (O diff do seu colega removeu essas views, mas elas são necessárias para o cadastro)
# ---

@login_required
def onboarding_formacao(request):
    """
    Passo 4: Adiciona Formação Acadêmica (70% progresso).
    """
    candidato = request.user.candidato
    progresso = 70

    if request.method == 'POST':
        form = FormacaoForm(request.POST)
        if form.is_valid():
            formacao = form.save(commit=False)
            formacao.candidato = candidato
            formacao.save()
            
            if 'continuar' in request.POST:
                return redirect('onboarding_skills') # Próximo passo
            else:
                return redirect('onboarding_formacao')
    else:
        form = FormacaoForm()

    formacoes_salvas = Formacao_Academica.objects.filter(candidato=candidato).order_by('-data_inicio')
    
    return render(request, 'usuarios/onboarding_formacao.html', {
        'form': form,
        'formacoes': formacoes_salvas,
        'progress': progresso
    })

@login_required
def onboarding_skills(request):
    """
    Passo 5: Adiciona Skills (85% progresso).
    """
    candidato = request.user.candidato
    progresso = 85

    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.candidato = candidato
            skill.save()
            
            if 'continuar' in request.POST:
                return redirect('onboarding_curriculo') # Próximo passo
            else:
                return redirect('onboarding_skills')
    else:
        form = SkillForm()

    skills_salvas = Skill.objects.filter(candidato=candidato)
    
    return render(request, 'usuarios/onboarding_skills.html', {
        'form': form,
        'skills': skills_salvas,
        'progress': progresso
    })

@login_required
def onboarding_curriculo(request):
    """
    Passo 6: Upload do Currículo PDF (100% progresso).
    """
    candidato = request.user.candidato
    progresso = 100

    if request.method == 'POST':
        # IMPORTANTE: request.FILES é necessário para uploads
        form = CurriculoForm(request.POST, request.FILES, instance=candidato)
        if form.is_valid():
            form.save()
            # Fim da "cutscene"! Redireciona para o painel principal.
            return redirect('home_candidato')
    else:
        form = CurriculoForm(instance=candidato)

    return render(request, 'usuarios/onboarding_curriculo.html', {
        'form': form,
        'progress': progresso
    })

# --- [IMPORTANTE] ---
# MANTENDO AS FUNÇÕES AJAX ORIGINAIS (para o home_candidato.html funcionar)

@login_required
def ajax_salvar_resumo(request):
    if request.method == 'POST':
        candidato = request.user.candidato
        texto_resumo = request.POST.get('resumo', '')
        
        Resumo_Profissional.objects.update_or_create(
            candidato=candidato,
            defaults={'texto': texto_resumo}
        )
        
        return JsonResponse({
            'status': 'success',
            'action': 'next_step'
        })
    return JsonResponse({'status': 'error', 'message': 'Método GET não permitido'})

@login_required
def ajax_salvar_experiencia(request):
    if request.method == 'POST':
        form = ExperienciaForm(request.POST)
        if form.is_valid():
            exp = form.save(commit=False)
            exp.candidato = request.user.candidato
            exp.save()
            
            if 'continuar' in request.POST:
                return JsonResponse({
                    'status': 'success',
                    'action': 'next_step'
                })
            else:
                return JsonResponse({
                    'status': 'success',
                    'action': 'add_another',
                    'list_id': 'lista-experiencias',
                    'saved_item_html': f'<p><strong>{exp.cargo}</strong> em {exp.empresa}</p>' 
                })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors.as_json()})
    return JsonResponse({'status': 'error', 'message': 'Método GET não permitido'})

@login_required
def ajax_salvar_formacao(request):
    if request.method == 'POST':
        form = FormacaoForm(request.POST)
        if form.is_valid():
            formacao = form.save(commit=False)
            formacao.candidato = request.user.candidato
            formacao.save()
            
            if 'continuar' in request.POST:
                return JsonResponse({'status': 'success', 'action': 'next_step'})
            else:
                return JsonResponse({
                    'status': 'success',
                    'action': 'add_another',
                    'list_id': 'lista-formacoes',
                    'saved_item_html': f'<p><strong>{formacao.nome_formacao}</strong> em {formacao.nome_instituicao}</p>'
                })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors.as_json()})
    return JsonResponse({'status': 'error', 'message': 'Método GET não permitido'})

@login_required
def ajax_salvar_skill(request):
    if request.method == 'POST':
        form = SkillForm(request.POST)
        if form.is_valid():
            skill = form.save(commit=False)
            skill.candidato = request.user.candidato
            skill.save()

            if 'continuar' in request.POST:
                return JsonResponse({'status': 'success', 'action': 'next_step'})
            else: # "Salvar e Adicionar Outro"
                return JsonResponse({
                    'status': 'success',
                    'action': 'add_another',
                    'list_id': 'lista-skills',
                    'saved_item_html': f'<p><strong>{skill.nome}</strong> ({skill.get_tipo_display()})</p>'
                })
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors.as_json()})
    return JsonResponse({'status': 'error', 'message': 'Método GET não permitido'})

@login_required
def ajax_salvar_curriculo(request):
    if request.method == 'POST':
        candidato = request.user.candidato
        form = CurriculoForm(request.POST, request.FILES, instance=candidato) 

        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'action': 'next_step'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors.as_json()})
    return JsonResponse({'status': 'error', 'message': 'Método GET não permitido'})

@transaction.atomic
def cadastrar_recrutador(request):
    """
    Processa o formulário de cadastro do Recrutador/Empresa.
    """
    if request.method == 'POST':
        form = RecrutadorCadastroForm(request.POST)
        
        if form.is_valid():
            data = form.cleaned_data
            
            try:
                empresa = Empresa.objects.create(
                    nome=data['nome_empresa'],
                    cnpj=data['cnpj'],
                    setor=data['setor'],
                    telefone=data['telefone'] 
                )
                
                user = Usuario.objects.create_user(
                    username=data['email'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    telefone=data['telefone'],
                    tipo_usuario='recrutador'
                )
                
                recrutador = Recrutador.objects.create(
                    usuario=user,
                    empresa=empresa
                )
                
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Bem-vindo, {user.first_name}! Perfil da empresa criado.')
                return redirect('home_recrutador')

            except IntegrityError as e:
                messages.error(request, f"Ocorreu um erro ao criar seu perfil: {e}")
            
    else:
        form = RecrutadorCadastroForm()
        
    return render(request, 'usuarios/cadastro_recrutador.html', {'form': form})


# --- FIM DAS FUNÇÕES AJAX ---


# ----------------------------------------------------
# 🔐 NOVOS ENDPOINTS DE API (DRF/JWT) - (Do Merge)
# ----------------------------------------------------

class ResumoProfissionalAPIView(APIView):
    """
    API para salvar/atualizar o Resumo Profissional do Candidato.
    Requer autenticação via JWT e o perfil Candidato.
    """
    permission_classes = [IsAuthenticated, IsCandidato] 
    
    def post(self, request):
        candidato = request.user.candidato
        texto_resumo = request.data.get('resumo', '') # Usa request.data
        
        Resumo_Profissional.objects.update_or_create(
            candidato=candidato,
            defaults={'texto': texto_resumo}
        )
        
        return Response({
            'status': 'success',
            'action': 'next_step'
        }, status=status.HTTP_200_OK)

    def get(self, request):
        return Response(
            {'status': 'error', 'message': 'Método não permitido'}, 
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

class ExperienciaProfissionalAPIView(APIView):
    """
    API para salvar/atualizar a Experiência Profissional do Candidato.
    Requer autenticação via JWT e o perfil Candidato.
    """
    permission_classes = [IsAuthenticated, IsCandidato] 
    
    def post(self, request):
        # --- CORREÇÃO DO MERGE ---
        # A lógica desta view estava faltando no diff do seu colega.
        # Pegamos a lógica da sua 'ajax_salvar_experiencia' e a adaptamos.
        
        candidato = request.user.candidato
        form = ExperienciaForm(request.data) # Usa request.data
        
        if form.is_valid():
            exp = form.save(commit=False)
            exp.candidato = candidato
            exp.save()
            
            if 'continuar' in request.data: # Usa request.data
                return Response({
                    'status': 'success',
                    'action': 'next_step'
                }, status=status.HTTP_200_OK)
            else:
                # "Salvar e Adicionar Outro"
                return Response({
                    'status': 'success',
                    'action': 'add_another',
                    'list_id': 'lista-experiencias',
                    'saved_item_html': f'<p><strong>{exp.cargo}</strong> em {exp.empresa}</p>' 
                }, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)
        # --- FIM DA CORREÇÃO ---

class FormacaoAPIView(APIView):
    """
    API para salvar/atualizar a Formação Acadêmica do Candidato.
    Requer autenticação via JWT e o perfil Candidato.
    """
    permission_classes = [IsAuthenticated, IsCandidato] 
    
    def post(self, request):
        candidato = request.user.candidato
        form = FormacaoForm(request.data) 
        
        if form.is_valid():
            formacao = form.save(commit=False)
            formacao.candidato = candidato
            formacao.save()
            
            if 'continuar' in request.data:
                return Response({'status': 'success', 'action': 'next_step'}, status=status.HTTP_200_OK)
            else:
                return Response({
                    'status': 'success',
                    'action': 'add_another',
                    'list_id': 'lista-formacoes',
                    'saved_item_html': f'<p><strong>{formacao.nome_formacao}</strong> em {formacao.nome_instituicao}</p>'
                }, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

class SkillAPIView(APIView):
    """
    API para salvar/atualizar as Skills do Candidato.
    Requer autenticação via JWT e o perfil Candidato.
    """
    permission_classes = [IsAuthenticated, IsCandidato] 
    
    def post(self, request):
        candidato = request.user.candidato
        form = SkillForm(request.data) 
        
        if form.is_valid():
            skill = form.save(commit=False)
            skill.candidato = candidato
            skill.save()

            if 'continuar' in request.data:
                return Response({'status': 'success', 'action': 'next_step'}, status=status.HTTP_200_OK)
            else: 
                return Response({
                    'status': 'success',
                    'action': 'add_another',
                    'list_id': 'lista-skills',
                    'saved_item_html': f'<p><strong>{skill.nome}</strong> ({skill.get_tipo_display()})</p>'
                }, status=status.HTTP_201_CREATED)
        else:
            return Response({'status': 'error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)

class CurriculoAPIView(APIView):
    """
    API para upload do Currículo PDF.
    Requer autenticação via JWT e o perfil Candidato.
    """
    permission_classes = [IsAuthenticated, IsCandidato] 
    
    def post(self, request):
        candidato = request.user.candidato
        # Para arquivos, usamos request.data e request.FILES
        form = CurriculoForm(request.data, request.FILES, instance=candidato) 
        
        if form.is_valid():
            form.save()
            return Response({'status': 'success', 'action': 'next_step'}, status=status.HTTP_200_OK)
        else:
            return Response({'status': 'error', 'errors': form.errors}, status=status.HTTP_400_BAD_REQUEST)


@login_required
@require_http_methods(["DELETE"])
def ajax_deletar_skill(request, skill_id):
    try:
        skill = Skill.objects.get(id=skill_id, candidato=request.user.candidato)
        skill.delete()
        return JsonResponse({'status': 'success'})
    except Skill.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Skill não encontrada'}, status=404)

@login_required
@require_http_methods(["DELETE"])
def ajax_deletar_experiencia(request, xp_id):
    try:
        exp = Experiencia.objects.get(id=xp_id, candidato=request.user.candidato)
        exp.delete()
        return JsonResponse({'status': 'success'})
    except Experiencia.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Experiência não encontrada'}, status=404)

@login_required
@require_http_methods(["DELETE"])
def ajax_deletar_formacao(request, edu_id):
    try:
        formacao = Formacao_Academica.objects.get(id=edu_id, candidato=request.user.candidato)
        formacao.delete()
        return JsonResponse({'status': 'success'})
    except Formacao_Academica.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Formação não encontrada'}, status=404)

@login_required
def perfil_publico(request, username):
    """
    Visualização pública (ou para recrutadores) do perfil do candidato.
    """
    # Busca o usuário pelo username (que é único)
    usuario_alvo = get_object_or_404(Usuario, username=username)
    
    # Tenta pegar o perfil de candidato dele
    try:
        candidato = usuario_alvo.candidato
    except Candidato.DoesNotExist:
        messages.error(request, 'Este usuário não possui um perfil de candidato.')
        return redirect('home_recrutador')

    # Pega os dados (Igual ao home_candidato, mas filtrando pelo candidato_alvo)
    try:
        resumo = candidato.resumo_profissional.texto
    except:
        resumo = "Sem resumo cadastrado."

    contexto = {
        'candidato_alvo': candidato, # Passamos o objeto candidato para pegar nome, etc.
        'texto_resumo': resumo,
        'hard_skills': Skill.objects.filter(candidato=candidato, tipo='hard'),
        'soft_skills': Skill.objects.filter(candidato=candidato, tipo='soft'),
        'experiencias': Experiencia.objects.filter(candidato=candidato).order_by('-data_inicio'),
        'formacoes': Formacao_Academica.objects.filter(candidato=candidato).order_by('-data_inicio'),
    }
    
    return render(request, 'usuarios/perfil_publico.html', contexto)

@login_required
def explorar_vagas(request):
    """
    Lista TODAS as vagas abertas no sistema.
    """
    vagas = Vaga.objects.filter(status=True).order_by('-data_publicacao')
    return render(request, 'vagas/explorar_vagas.html', {'vagas': vagas})

@login_required
def ver_empresa(request, empresa_id):
    """
    Perfil público da empresa com sistema de avaliações.
    """
    empresa = get_object_or_404(Empresa, id=empresa_id)
    
    # Processar Avaliação (POST)
    if request.method == 'POST':
        try:
            nota = int(request.POST.get('nota'))
            comentario = request.POST.get('comentario')
            
            AvaliacaoEmpresa.objects.update_or_create(
                empresa=empresa,
                candidato=request.user.candidato,
                defaults={'nota': nota, 'comentario': comentario}
            )
            messages.success(request, 'Avaliação enviada com sucesso!')
        except Exception as e:
            messages.error(request, f'Erro ao avaliar: {e}')
        return redirect('ver_empresa', empresa_id=empresa.id)

    # Dados para exibição
    avaliacoes = empresa.avaliacoes.all().order_by('-data')
    media = avaliacoes.aggregate(Avg('nota'))['nota__avg']
    
    # Verifica se o usuário já avaliou
    minha_avaliacao = avaliacoes.filter(candidato=request.user.candidato).first()

    contexto = {
        'empresa': empresa,
        'vagas_abertas': Vaga.objects.filter(empresa=empresa, status=True),
        'avaliacoes': avaliacoes,
        'media_nota': round(media, 1) if media else "N/A",
        'minha_avaliacao': minha_avaliacao
    }
    return render(request, 'vagas/ver_empresa.html', contexto)

# --- VIEWS PARA RECUPERAÇÃO DE SENHA ---
def recuperar_senha_view(request):
    """
    Renderiza a página inicial de recuperação de senha (Pedir Código).
    """
    return render(request, 'usuarios/recuperar_senha.html')

def nova_senha_view(request):
    """
    Renderiza a página de criação de nova senha após a validação do código.
    """
    return render(request, 'usuarios/nova_senha.html')
