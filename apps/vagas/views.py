from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import IntegrityError
from .models import Vaga, Candidatura
from apps.usuarios.models import Recrutador, Candidato, Empresa
from .forms import VagaForm
from apps.usuarios.forms import (
    ExperienciaForm, FormacaoForm, SkillForm, CurriculoForm
)
from apps.matching.engine import calcular_similaridade_tags

# Imports para o painel_admin (que estavam faltando)
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.utils import timezone
import datetime


def landing_page(request):
    """
    Renderiza a Home Page (Landing Page) do site.
    """
    if request.user.is_authenticated:
        if request.user.tipo_usuario == 'candidato':
            return redirect('home_candidato')
        elif request.user.tipo_usuario == 'recrutador':
            return redirect('home_recrutador')
    
    total_candidatos = Candidato.objects.count()
    total_vagas = Vaga.objects.filter(status=True).count()
    total_empresas = Empresa.objects.count()

    contexto = {
        'total_candidatos': total_candidatos,
        'total_vagas': total_vagas,
        'total_empresas': total_empresas,
    }
    return render(request, 'vagas/landing_page.html', contexto)

@login_required 
def criar_vaga(request):
    """
    View para um Recrutador criar uma nova vaga.
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado. Esta página é apenas para recrutadores.')
        return redirect('home_candidato') 

    recrutador_logado = get_object_or_404(Recrutador, usuario=request.user)

    if request.method == 'POST':
        form = VagaForm(request.POST, empresa=recrutador_logado.empresa)
        
        if form.is_valid():
            vaga = form.save(commit=False, recrutador=recrutador_logado)
            vaga.save()
            messages.success(request, 'Vaga criada com sucesso!')
            return redirect('home_recrutador')
    else:
        form = VagaForm(empresa=recrutador_logado.empresa)

    return render(request, 'vagas/criar_vaga.html', {'form': form})
    
@login_required
def home_candidato(request):
    """
    Painel do Candidato.
    """
    if request.user.tipo_usuario != 'candidato':
        messages.error(request, 'Acesso negado.')
        return redirect('home_recrutador')

    lista_de_vagas = Vaga.objects.filter(status=True).order_by('-data_publicacao')
    
    contexto = {
        'vagas': lista_de_vagas,
        'experiencia_form': ExperienciaForm(),
        'formacao_form': FormacaoForm(),
        'skill_form': SkillForm(),
        'curriculo_form': CurriculoForm(),
    }
    
    return render(request, 'vagas/home_candidato.html', contexto)

@login_required
def home_recrutador(request):
    """
    Painel do Recrutador, lista as vagas criadas por ele. (R do CRUD)
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado.')
        return redirect('home_candidato')

    try:
        recrutador = request.user.recrutador
    except Recrutador.DoesNotExist:
        messages.error(request, 'Você não possui um perfil de recrutador associado.')
        return redirect('home_candidato')

    minhas_vagas = Vaga.objects.filter(recrutador=recrutador)
    
    contexto = {
        'vagas': minhas_vagas
    }
    return render(request, 'vagas/home_recrutador.html', contexto)

@login_required
def editar_vaga(request, vaga_id):
    """
    View para um Recrutador editar uma de suas vagas. (U do CRUD)
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado.')
        return redirect('home_candidato')
    
    vaga = get_object_or_404(Vaga, id=vaga_id)
    
    if vaga.recrutador.usuario != request.user:
        messages.error(request, 'Você não tem permissão para editar esta vaga.')
        return redirect('home_recrutador')

    recrutador_logado = request.user.recrutador

    if request.method == 'POST':
        form = VagaForm(request.POST, instance=vaga, empresa=recrutador_logado.empresa)
        if form.is_valid():
            form.save(recrutador=recrutador_logado)
            messages.success(request, 'Vaga atualizada com sucesso!')
            return redirect('home_recrutador')
    else:
        form = VagaForm(instance=vaga, empresa=recrutador_logado.empresa)

    contexto = {
        'form': form,
        'vaga': vaga 
    }
    return render(request, 'vagas/editar_vaga.html', contexto)

@login_required
def deletar_vaga(request, vaga_id):
    """
    View para um Recrutador deletar uma de suas vagas. (D do CRUD)
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado.')
        return redirect('home_candidato')
    
    vaga = get_object_or_404(Vaga, id=vaga_id)
    
    if vaga.recrutador.usuario != request.user:
        messages.error(request, 'Você não tem permissão para deletar esta vaga.')
        return redirect('home_recrutador')

    if request.method == 'POST':
        vaga.delete()
        messages.success(request, 'Vaga deletada com sucesso!')
        return redirect('home_recrutador')
    
    contexto = {
        'vaga': vaga
    }
    return render(request, 'vagas/deletar_vaga.html', contexto)
    
@login_required
def aplicar_vaga(request, vaga_id):
    """
    View para um Candidato se aplicar a uma vaga.
    """
    if request.user.tipo_usuario != 'candidato':
        messages.error(request, 'Apenas candidatos podem se candidatar a vagas.')
        return redirect('home_recrutador')

    if request.method == 'POST':
        try:
            vaga = get_object_or_404(Vaga, id=vaga_id, status=True)
            candidato = request.user.candidato
            
            Candidatura.objects.create(
                candidato=candidato,
                vaga=vaga,
                status='Enviada'
            )
            messages.success(request, 'Candidatura enviada com sucesso! Boa sorte.')
        
        except IntegrityError:
            messages.warning(request, 'Você já se candidatou para esta vaga.')
        
        except Candidato.DoesNotExist:
            messages.error(request, 'Você não possui um perfil de candidato para se candidatar.')
        
        except Exception as e:
            messages.error(request, f'Ocorreu um erro: {e}')
            
    return redirect('home_candidato')

# --- CORREÇÃO ---
# Removida a função duplicada e adicionado o login_required
@login_required
def perfil_empresa(request):
    """
    View para o Recrutador editar o perfil da empresa.
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado.')
        return redirect('home_candidato')
        
    return render(request, 'vagas/perfil_empresa.html')

@login_required
def ver_candidatos_vaga(request, vaga_id):
    """
    View para o Recrutador ver os candidatos que aplicaram
    para uma vaga específica, ordenados por score de matching.
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado.')
        return redirect('home_candidato')

    vaga = get_object_or_404(Vaga, id=vaga_id)

    if vaga.recrutador.usuario != request.user:
        messages.error(request, 'Você não tem permissão para ver esta página.')
        return redirect('home_recrutador')

    # --- CORREÇÃO BUG 0% ---
    # Adicionando de volta a otimização de performance
    candidaturas = Candidatura.objects.filter(vaga=vaga).select_related(
        'candidato',
        'candidato__resumo_profissional'
    ).prefetch_related(
        'candidato__skills',
        'candidato__experiencias',
        'candidato__formacoes'
    )
    candidatos_com_score = []
    for candidatura in candidaturas:
        candidato = candidatura.candidato
        score = calcular_similaridade_tags(vaga, candidato)

        candidatos_com_score.append({
            'candidato': candidato,
            'score': score,
            'data_aplicacao': candidatura.data_candidatura,
            'status': candidatura.status
        })

    candidatos_ordenados = sorted(
        candidatos_com_score, 
        key=lambda item: item['score'], 
        reverse=True
    )

    contexto = {
        'vaga': vaga,
        'candidatos_ordenados': candidatos_ordenados
    }

    return render(request, 'vagas/ver_candidatos_vaga.html', contexto)

@login_required
def radar_de_talentos(request):
    """
    A nova tela de "Radar de Talentos" com a "Engine de IA".
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado.')
        return redirect('home_candidato')

    try:
        recrutador = request.user.recrutador
    except Recrutador.DoesNotExist:
        messages.error(request, 'Você não possui um perfil de recrutador associado.')
        return redirect('home_candidato')

    minhas_vagas = Vaga.objects.filter(recrutador=recrutador, status=True)
    candidatos_ordenados = []
    total_encontrados = 0
    vaga_selecionada_id = None

    if request.method == 'POST':
        vaga_selecionada_id = request.POST.get('vaga_id')
        if vaga_selecionada_id:
            vaga = get_object_or_404(Vaga, id=vaga_selecionada_id, recrutador=recrutador)
            
            # --- CORREÇÃO BUG 0% ---
            # Adicionando de volta a otimização de performance
            todos_os_candidatos = Candidato.objects.all().select_related(
                'usuario', 'resumo_profissional'
            ).prefetch_related(
                'skills', 'experiencias', 'formacoes'
            )

            candidatos_com_score = []
            for candidato in todos_os_candidatos:
                score = calcular_similaridade_tags(vaga, candidato)
                
                if score > 20: 
                    candidatos_com_score.append({
                        'candidato': candidato,
                        'score': score
                    })

            candidatos_ordenados = sorted(
                candidatos_com_score, 
                key=lambda item: item['score'], 
                reverse=True
            )
            total_encontrados = len(candidatos_ordenados)
            vaga_selecionada_id = int(vaga_selecionada_id)

    contexto = {
        'minhas_vagas': minhas_vagas,
        'candidatos_ordenados': candidatos_ordenados,
        'total_encontrados': total_encontrados,
        'vaga_selecionada_id': vaga_selecionada_id
    }
    
    return render(request, 'vagas/radar_de_talentos.html', contexto)

@login_required
def planos_empresa(request):
    """
    View para a página de planos da empresa.
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado.')
        return redirect('home_candidato')
        
    # --- CORREÇÃO ---
    # O caminho do template precisa do prefixo da pasta 'vagas/'
    return render(request, "vagas/planos_empresa.html")

# --- CORREÇÃO ---
# Adicionando de volta a view 'painel_admin' que estava faltando
@login_required
def painel_admin(request):
    """
    View para o novo painel de administrador customizado.
    Valida se o usuário é um 'superuser' ou 'staff'.
    """
    
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'Acesso negado. Esta página é restrita.')
        if request.user.tipo_usuario == 'candidato':
            return redirect('home_candidato')
        elif request.user.tipo_usuario == 'recrutador':
            return redirect('home_recrutador')
        else:
            return redirect('landing_page') # Fallback

    um_mes_atras = timezone.now() - datetime.timedelta(days=30)
    
    novos_candidatos = Candidato.objects.filter(usuario__date_joined__gte=um_mes_atras).count()
    novas_empresas = Empresa.objects.filter(id__in=Recrutador.objects.filter(usuario__date_joined__gte=um_mes_atras).values_list('empresa_id', flat=True)).count()
    vagas_ativas = Vaga.objects.filter(status=True).count()
    novas_candidaturas = Candidatura.objects.filter(data_candidatura__gte=um_mes_atras).count()

    ultimos_candidatos = Candidato.objects.all().order_by('-usuario__date_joined')[:10]
    ultimas_empresas = Empresa.objects.all().order_by('-id')[:10] 
    
    candidatos_recentes = Candidato.objects.all().order_by('-usuario__date_joined')[:5]
    empresas_recentes = Empresa.objects.all().order_by('-id')[:5]
    vagas_recentes = Vaga.objects.all().order_by('-data_publicacao')[:5]

    contexto = {
        'nome_admin': request.user.first_name or request.user.username,
        
        'stat_novos_candidatos': novos_candidatos,
        'stat_novas_empresas': novas_empresas,
        'stat_vagas_ativas': vagas_ativas,
        'stat_novas_candidaturas': novas_candidaturas,
        
        'lista_candidatos': ultimos_candidatos,
        'lista_empresas': ultimas_empresas,
        
        'atividades_candidatos': candidatos_recentes,
        'atividades_empresas': empresas_recentes,
        'atividades_vagas': vagas_recentes,
    }
    
    return render(request, 'vagas/painel_admin.html', contexto)
