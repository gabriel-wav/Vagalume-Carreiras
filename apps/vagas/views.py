from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vaga, Candidatura
from .forms import VagaForm
from apps.usuarios.models import Recrutador, Candidato
from django.http import HttpResponse, Http404
from django.db import IntegrityError
from apps.usuarios.forms import ExperienciaForm, FormacaoForm
from apps.usuarios.models import Candidato, Empresa
from .models import Vaga
from apps.matching.engine import calcular_similaridade 
from apps.usuarios.forms import ExperienciaForm, FormacaoForm


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
    Agora também é a central de Onboarding e calcula o Matching.
    """
    # Controle de Permissão
    if request.user.tipo_usuario != 'candidato':
        messages.error(request, 'Acesso negado.')
        return redirect('home_recrutador')

    # Pega o perfil de candidato logado
    candidato = request.user.candidato

    # Busca TODAS as vagas que estão abertas (status=True)
    lista_de_vagas = Vaga.objects.filter(status=True)

    # --- AQUI COMEÇA A MÁGICA DA SEMANA 7 ---
    vagas_com_match = []

    for vaga in lista_de_vagas:
        # 1. Calcula o score usando a engine
        score = calcular_similaridade(vaga, candidato)

        # 2. Adiciona a vaga e seu score na lista
        vagas_com_match.append({
            'vaga': vaga,
            'match_score': score
        })

    # 3. ORDENA a lista: vagas com maior score primeiro!
    vagas_ordenadas = sorted(
        vagas_com_match, 
        key=lambda item: item['match_score'], 
        reverse=True
    )
    # --- FIM DA MÁGICA ---

    # Prepara os formulários vazios para o onboarding (como antes)
    contexto = {
        'vagas_com_match': vagas_ordenadas, # Manda a lista ordenada!
        'experiencia_form': ExperienciaForm(),
        'formacao_form': FormacaoForm(),
        # (adicione os outros forms aqui quando criá-los)
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