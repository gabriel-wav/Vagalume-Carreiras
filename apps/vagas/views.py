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



def landing_page(request):
    """
    Renderiza a Home Page (Landing Page) do site.
    
    Se o usuário já estiver logado, redireciona ele para
    o painel correto (candidato ou recrutador).
    """
    if request.user.is_authenticated:
        # Usuário está logado
        if request.user.tipo_usuario == 'candidato':
            return redirect('home_candidato')
        elif request.user.tipo_usuario == 'recrutador':
            return redirect('home_recrutador')
    
    # --- LÓGICA DOS STATS ---
    # Busca os números reais do seu banco de dados
    total_candidatos = Candidato.objects.count()
    total_vagas = Vaga.objects.filter(status=True).count() # Conta só vagas abertas
    total_empresas = Empresa.objects.count()

    contexto = {
        'total_candidatos': total_candidatos,
        'total_vagas': total_vagas,
        'total_empresas': total_empresas,
    }
    
    # Se não estiver logado, mostra a landing page com os stats
    return render(request, 'vagas/landing_page.html', contexto)

@login_required 
def criar_vaga(request):
    """
    View para um Recrutador criar uma nova vaga.
    (VERSÃO ATUALIZADA para funcionar com o novo forms.py)
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado. Esta página é apenas para recrutadores.')
        return redirect('home_candidato') 

    # Pega o perfil do recrutador logado para passar para o formulário
    recrutador_logado = get_object_or_404(Recrutador, usuario=request.user)

    if request.method == 'POST':
        # Passa a 'empresa' para o __init__ do formulário
        form = VagaForm(request.POST, empresa=recrutador_logado.empresa)
        
        if form.is_valid():
            # Passa o 'recrutador' para o save customizado do formulário
            vaga = form.save(commit=False, recrutador=recrutador_logado)
            vaga.save() # O save customizado já preencheu empresa e recrutador
            
            messages.success(request, 'Vaga criada com sucesso!')
            return redirect('home_recrutador')
    else:
        # Passa a 'empresa' para o __init__ do formulário
        form = VagaForm(empresa=recrutador_logado.empresa)

    return render(request, 'vagas/criar_vaga.html', {'form': form})
    
@login_required
def home_candidato(request):
    """
    Painel do Candidato.
    (Versão LIMPA, sem o "radar" de score para corrigir o crash).
    """
    if request.user.tipo_usuario != 'candidato':
        messages.error(request, 'Acesso negado.')
        return redirect('home_recrutador')

    # --- VOLTAMOS AO CÓDIGO SIMPLES ---
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
        # Busca o perfil 'Recrutador' associado ao 'Usuario' logado
        recrutador = request.user.recrutador
    except Recrutador.DoesNotExist:
        messages.error(request, 'Você não possui um perfil de recrutador associado.')
        return redirect('home_candidato')

    # Filtra as vagas: pega apenas aquelas onde o 'recrutador' é o usuário logado
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
    
    # Busca a vaga específica no banco, ou retorna um erro 404
    vaga = get_object_or_404(Vaga, id=vaga_id)
    
    # CONTROLE DE PERMISSÃO:
    # Garante que o recrutador logado só possa editar as SUAS PRÓPRIAS vagas
    if vaga.recrutador.usuario != request.user:
        messages.error(request, 'Você não tem permissão para editar esta vaga.')
        return redirect('home_recrutador')

    recrutador_logado = request.user.recrutador

    if request.method == 'POST':
        # Popula o formulário com os dados enviados (request.POST) e
        # com a instância da vaga que estamos editando
        form = VagaForm(request.POST, instance=vaga, empresa=recrutador_logado.empresa)
        if form.is_valid():
            form.save(recrutador=recrutador_logado)
            messages.success(request, 'Vaga atualizada com sucesso!')
            return redirect('home_recrutador')
    else:
        # Se for um GET, apenas mostra o formulário pré-preenchido
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
    
    # Busca a vaga ou retorna erro 404
    vaga = get_object_or_404(Vaga, id=vaga_id)
    
    # CONTROLE DE PERMISSÃO:
    # Garante que o recrutador só possa deletar as SUAS PRÓPRIAS vagas
    if vaga.recrutador.usuario != request.user:
        messages.error(request, 'Você não tem permissão para deletar esta vaga.')
        return redirect('home_recrutador')

    if request.method == 'POST':
        # Se o usuário confirmou no formulário (clicou no botão "Confirmar")
        vaga.delete()
        messages.success(request, 'Vaga deletada com sucesso!')
        return redirect('home_recrutador') # Volta para o painel
    
    # Se for um GET, apenas mostra a página de confirmação
    contexto = {
        'vaga': vaga
    }
    return render(request, 'vagas/deletar_vaga.html', contexto)
    
@login_required
def aplicar_vaga(request, vaga_id):
    """
    View para um Candidato se aplicar a uma vaga. (C do CRUD de Candidatura)
    Esta view é chamada por um formulário POST.
    """
    # 1. Controle de Permissão
    if request.user.tipo_usuario != 'candidato':
        messages.error(request, 'Apenas candidatos podem se candidatar a vagas.')
        return redirect('home_recrutador')

    # 2. Garante que o método é POST
    if request.method == 'POST':
        try:
            # 3. Pega os objetos necessários
            vaga = get_object_or_404(Vaga, id=vaga_id, status=True) # Só pode se candidatar a vagas abertas
            candidato = request.user.candidato # Pega o perfil de candidato do usuário logado
            
            # 4. Tenta criar a candidatura (Fluxo Principal UC05)
            # A checagem de duplicidade é feita pelo 'unique_together' no model
            Candidatura.objects.create(
                candidato=candidato,
                vaga=vaga,
                status='Enviada' # Define o status inicial
            )
            messages.success(request, 'Candidatura enviada com sucesso! Boa sorte.')
        
        except IntegrityError:
            # 5. Fluxo Alternativo A1 (Candidatura Duplicada)
            # O 'unique_together' no model
            # falhou, o que significa que a candidatura já existe.
            messages.warning(request, 'Você já se candidatou para esta vaga.')
        
        except Candidato.DoesNotExist:
            messages.error(request, 'Você não possui um perfil de candidato para se candidatar.')
        
        except Exception as e:
            messages.error(request, f'Ocorreu um erro: {e}')
            
    # 6. Redireciona de volta para a lista de vagas
    return redirect('home_candidato')
  
  
def perfil_empresa(request):
    return render(request, 'vagas/perfil_empresa.html')

@login_required
def ver_candidatos_vaga(request, vaga_id):
    """
    View para o Recrutador ver os candidatos que aplicaram
    para uma vaga específica, ordenados por score de matching.
    """
    # 1. Checa se é um recrutador
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado.')
        return redirect('home_candidato')

    # 2. Pega a vaga
    vaga = get_object_or_404(Vaga, id=vaga_id)

    # 3. VERIFICAÇÃO DE PERMISSÃO (CRUCIAL!)
    # Garante que o recrutador só possa ver os candidatos das SUAS vagas.
    if vaga.recrutador.usuario != request.user:
        messages.error(request, 'Você não tem permissão para ver esta página.')
        return redirect('home_recrutador')

    # 4. Pega todas as candidaturas para esta vaga
    candidaturas = Candidatura.objects.filter(vaga=vaga)

    # 5. RODA O "RADAR" (O "Grande Pã")
    candidatos_com_score = []
    for candidatura in candidaturas:
        candidato = candidatura.candidato
        # Reutiliza a engine de matching!
        score = calcular_similaridade_tags(vaga, candidato)

        candidatos_com_score.append({
            'candidato': candidato,
            'score': score,
            'data_aplicacao': candidatura.data_candidatura,
            'status': candidatura.status
        })

    # 6. Ordena a lista pelo score, do maior para o menor
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
    A nova tela de "Radar de Talentos" com a "Engine de Tags".
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
            todos_os_candidatos = Candidato.objects.all()

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

def perfil_empresa(request):
    return render(request, 'vagas/perfil_empresa.html')

def planos_empresa(request):
    return render(request, "planos_empresa.html")


