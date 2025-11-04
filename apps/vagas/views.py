from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Vaga, Candidatura
from .forms import VagaForm
from apps.usuarios.models import Recrutador
from django.http import HttpResponse


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
    Painel do Candidato, lista TODAS as vagas abertas. (R do CRUD)
    """
    # Controle de Permissão
    if request.user.tipo_usuario != 'candidato':
        messages.error(request, 'Acesso negado.')
        # Se um recrutador tentar acessar, joga ele de volta para o painel dele
        return redirect('home_recrutador')

    # Busca no banco:
    # 1. Filtra apenas vagas com status=True (Abertas)
    # 2. Ordena pela data de publicação, da mais nova para a mais antiga
    lista_de_vagas = Vaga.objects.filter(status=True).order_by('-data_publicacao')
    
    contexto = {
        'vagas': lista_de_vagas
    }
    # Renderiza o novo template que vamos criar
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

    