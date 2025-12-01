from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import IntegrityError
from .models import Vaga, Candidatura, Plano
from apps.usuarios.models import Recrutador, Candidato, Empresa
from .forms import VagaForm
from apps.usuarios.forms import (
    ExperienciaForm,
    FormacaoForm,
    SkillForm,
    CurriculoForm,
    PerfilUsuarioForm,
    PerfilCandidatoForm,
)
from apps.matching.engine import calcular_similaridade_tags
from apps.usuarios.models import Resumo_Profissional
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.utils import timezone
import datetime
from apps.usuarios.models import (
    Resumo_Profissional,
    Skill,
    Experiencia,
    Formacao_Academica,
    Redes_Sociais,
    Usuario,
)
from django.db.models import Avg
from apps.usuarios.models import AvaliacaoEmpresa
from django.db.models import Count
from django.http import JsonResponse
from .ai_advisor import gerar_dicas_perfil
from django.db.models import Q


def get_texto_candidato(candidato):
    """
    Extrai todo o texto relevante do perfil do candidato:
    Resumo profissional + Experiências + Skills.
    """
    textos = []
    
    # Resumo Profissional
    resumo = getattr(candidato, 'resumo_profissional', None)
    if resumo and resumo.texto:
        textos.append(resumo.texto)
    
    # Experiências
    experiencias = Experiencia.objects.filter(candidato=candidato)
    for exp in experiencias:
        textos.append(f"{exp.cargo} em {exp.empresa}")
        if exp.descricao:
            textos.append(exp.descricao)
    
    # Skills
    skills = Skill.objects.filter(candidato=candidato)
    skill_names = [skill.nome for skill in skills]
    if skill_names:
        textos.append(", ".join(skill_names))
    
    return " ".join(textos)


def landing_page(request):
    """
    Renderiza a Home Page com dados reais e categorias dinâmicas.
    """
    # Estatísticas Gerais
    total_candidatos = Candidato.objects.count()
    total_vagas = Vaga.objects.filter(status=True).count()
    total_empresas = Empresa.objects.count()

    # Vagas Recentes (para os cards)
    vagas_recentes = Vaga.objects.filter(status=True).order_by('-data_publicacao')[:6]

    top_cargos = Vaga.objects.filter(status=True).values('titulo').annotate(total=Count('id')).order_by('-total')[:5]

    top_setores = Vaga.objects.filter(status=True).values('empresa__setor').annotate(total=Count('id')).order_by('-total')[:8]

    context = {
        'total_candidatos': total_candidatos,
        'total_vagas': total_vagas,
        'total_empresas': total_empresas,
        'vagas_recentes': vagas_recentes,
        
        # Novos dados para o template
        'top_cargos': top_cargos,
        'top_setores': top_setores,
    }
    
    return render(request, 'vagas/landing_page.html', context)

@login_required
def deletar_comentario(request, comentario_id):
    """
    Permite que Admins ou a própria Empresa dona do perfil apaguem comentários.
    """
    comentario = get_object_or_404(AvaliacaoEmpresa, id=comentario_id)
    empresa_dona = comentario.empresa
    
    # Verifica Permissões
    is_admin = request.user.is_staff or request.user.is_superuser
    is_dono = False
    
    if request.user.tipo_usuario == 'recrutador':
        try:
            # Verifica se o recrutador logado pertence à empresa do comentário
            if request.user.recrutador.empresa == empresa_dona:
                is_dono = True
        except:
            pass

    if is_admin or is_dono:
        comentario.delete()
        messages.success(request, 'Comentário removido com sucesso.')
    else:
        messages.error(request, 'Você não tem permissão para apagar este comentário.')
    
    return redirect('ver_empresa', empresa_id=empresa_dona.id)

# Em apps/vagas/views.py

@login_required
def criar_vaga(request):
    """
    View para um Recrutador criar uma nova vaga.
    AGORA COM BLOQUEIO DE PLANO FUNCIONAL.
    """
    # 1. Verifica se é recrutador
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado. Esta página é apenas para recrutadores.')
        return redirect('home_candidato')

    # 2. Pega os dados da empresa
    recrutador_logado = get_object_or_404(Recrutador, usuario=request.user)
    empresa = recrutador_logado.empresa

    # --- TRAVA DE SEGURANÇA DO PLANO ---
    # Conta quantas vagas ABERTAS (status=True) essa empresa já tem
    vagas_ativas = Vaga.objects.filter(empresa=empresa, status=True).count()

    # Se o plano for 'basico' e já tiver 1 ou mais vagas... BLOQUEIA.
    if empresa.plano_assinado == 'basico' and vagas_ativas >= 1:
        messages.warning(
            request, 
            f'🚫 Limite do Plano Básico atingido! Você já tem {vagas_ativas} vaga ativa. '
            'Faça um upgrade para o Plano Intermediário ou Premium para continuar contratando.'
        )
        return redirect('planos_empresa') 
@login_required 
def criar_vaga(request):
    """
    View para um Recrutador criar uma nova vaga.
    INCLUI A REGRA DE NEGÓCIO: Plano Básico = Máx 1 Vaga.
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, 'Acesso negado. Esta página é apenas para recrutadores.')
        return redirect('home_candidato') 

    # Obtém o recrutador e a empresa
    recrutador_logado = get_object_or_404(Recrutador, usuario=request.user)
    empresa = recrutador_logado.empresa

    # --- REGRA DE BLOQUEIO DE PLANO ---
    # Conta quantas vagas 'Abertas' (status=True) essa empresa já tem
    vagas_ativas = Vaga.objects.filter(empresa=empresa, status=True).count()
    
    # Se for Plano Básico e já tiver 1 ou mais vagas ativas...
    if empresa.plano_assinado == 'basico' and vagas_ativas >= 1:
        messages.warning(
            request, 
            '🛑 Limite do Plano Básico atingido! Você já tem 1 vaga ativa. '
            'Para publicar mais vagas, faça um upgrade para o Plano Intermediário ou Premium.'
        )
        # Redireciona OBRIGATORIAMENTE para a escolha de planos
        return redirect('planos_empresa') 
    # ----------------------------------

    if request.method == 'POST':
        form = VagaForm(request.POST, empresa=empresa)
        
        if form.is_valid():
            vaga = form.save(commit=False, recrutador=recrutador_logado)
            vaga.save()
            messages.success(request, 'Vaga criada com sucesso!')
            return redirect('home_recrutador')
    else:
        form = VagaForm(empresa=empresa)

    return render(request, 'vagas/criar_vaga.html', {'form': form})

    return render(request, 'vagas/criar_vaga.html', {'form': form})

@login_required
def home_candidato(request):
    if request.user.tipo_usuario != "candidato":
        messages.error(request, "Acesso negado.")
        return redirect("home_recrutador")

    candidato = request.user.candidato

    # --- SALVAR PERFIL ---
    # Se for POST e não tiver 'continuar' (que é do onboarding), é edição de perfil
    if request.method == "POST" and "continuar" not in request.POST:
        perfil_user_form = PerfilUsuarioForm(request.POST, instance=request.user)
        perfil_candidato_form = PerfilCandidatoForm(request.POST, instance=candidato)

        if perfil_user_form.is_valid() and perfil_candidato_form.is_valid():
            perfil_user_form.save()
            perfil_candidato_form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect("home_candidato")
        else:
            messages.error(request, "Erro ao atualizar. Verifique os dados.")

    # --- PREPARAÇÃO DOS DADOS PARA EXIBIÇÃO ---

    # Forms para Edição (Preenchidos com dados atuais)
    perfil_user_form = PerfilUsuarioForm(instance=request.user)
    perfil_candidato_form = PerfilCandidatoForm(instance=candidato)

    # Forms para o Onboarding (Vazios)
    experiencia_form = ExperienciaForm()
    formacao_form = FormacaoForm()
    skill_form = SkillForm()
    curriculo_form = CurriculoForm()

    # Dados do Currículo (Para leitura - Versão Segura)
    resumo = getattr(candidato, "resumo_profissional", None)
    texto_resumo = resumo.texto if resumo else "Nenhum resumo cadastrado."

    contexto = {
        "vagas": Vaga.objects.filter(status=True).order_by("-data_publicacao"),
        # Forms
        "perfil_user_form": perfil_user_form,
        "perfil_candidato_form": perfil_candidato_form,
        "experiencia_form": experiencia_form,
        "formacao_form": formacao_form,
        "skill_form": skill_form,
        "curriculo_form": curriculo_form,
        # Dados Visuais (Ordenados)
        "texto_resumo": texto_resumo,
        "hard_skills": Skill.objects.filter(candidato=candidato, tipo="hard"),
        "soft_skills": Skill.objects.filter(candidato=candidato, tipo="soft"),
        "experiencias": Experiencia.objects.filter(candidato=candidato).order_by(
            "-data_inicio"
        ),
        "formacoes": Formacao_Academica.objects.filter(candidato=candidato).order_by(
            "-data_inicio"
        ),
    }

    return render(request, "vagas/home_candidato.html", contexto)


@login_required
def home_recrutador(request):
    """
    Painel do Recrutador.
    Agora busca o plano atual da empresa para mostrar na Badge.
    Painel do Recrutador, lista as vagas criadas por ele. (R do CRUD)
    Adiciona o plano atual da empresa ao contexto.
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(request, "Acesso negado.")
        return redirect("home_candidato")

    try:
        recrutador = request.user.recrutador
        empresa = recrutador.empresa # Pega a empresa
        
        # --- LÓGICA DO PLANO ---
        # Dicionário para traduzir 'premium' -> 'Plano Premium'
        # 1. Obter a Empresa do Recrutador
        empresa = recrutador.empresa

        # 2. Dicionário para formatar o nome do plano
        planos_nomes = {
            "basico": "Plano Básico",
            "intermediario": "Plano Intermediário",
            "premium": "Plano Premium"
        }
        
        # Pega o código do banco (ex: 'premium')
        slug = getattr(empresa, 'plano_assinado', 'basico')
        
        # Traduz para o nome bonito
        plano_atual_nome = planos_nomes.get(slug, "Plano Básico")
        # -----------------------

        plano_atual_slug = empresa.plano_assinado 
        # Obtém o nome amigável. Usa 'Nenhum Plano' como fallback
        plano_atual_nome = planos_nomes.get(plano_atual_slug, "Nenhum Plano") 

    except Recrutador.DoesNotExist:
        messages.error(request, "Você não possui um perfil de recrutador.")
        return redirect("home_candidato")

    minhas_vagas = Vaga.objects.filter(recrutador=recrutador)

    contexto = {
        "vagas": minhas_vagas,
        "plano_atual_nome": plano_atual_nome, # <--- ENVIANDO PARA O HTML
    }
    
    return render(request, "vagas/home_recrutador.html", contexto)
    
    contexto = {
        'vagas': minhas_vagas,
        # 3. Adiciona o nome do plano ao contexto
        'plano_atual_nome': plano_atual_nome 
    }
    return render(request, 'vagas/home_recrutador.html', contexto)

@login_required
def editar_vaga(request, vaga_id):
    """
    View para um Recrutador editar uma de suas vagas. (U do CRUD)
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(request, "Acesso negado.")
        return redirect("home_candidato")

    vaga = get_object_or_404(Vaga, id=vaga_id)

    if vaga.recrutador.usuario != request.user:
        messages.error(request, "Você não tem permissão para editar esta vaga.")
        return redirect("home_recrutador")

    recrutador_logado = request.user.recrutador

    if request.method == "POST":
        form = VagaForm(request.POST, instance=vaga, empresa=recrutador_logado.empresa)
        if form.is_valid():
            form.save(recrutador=recrutador_logado)
            messages.success(request, "Vaga atualizada com sucesso!")
            return redirect("home_recrutador")
    else:
        form = VagaForm(instance=vaga, empresa=recrutador_logado.empresa)

    contexto = {"form": form, "vaga": vaga}
    return render(request, "vagas/editar_vaga.html", contexto)


@login_required
def deletar_vaga(request, vaga_id):
    """
    View para um Recrutador deletar uma de suas vagas. (D do CRUD)
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(request, "Acesso negado.")
        return redirect("home_candidato")

    vaga = get_object_or_404(Vaga, id=vaga_id)

    if vaga.recrutador.usuario != request.user:
        messages.error(request, "Você não tem permissão para deletar esta vaga.")
        return redirect("home_recrutador")

    if request.method == "POST":
        vaga.delete()
        messages.success(request, "Vaga deletada com sucesso!")
        return redirect("home_recrutador")

    contexto = {"vaga": vaga}
    return render(request, "vagas/deletar_vaga.html", contexto)


@login_required
def aplicar_vaga(request, vaga_id):
    """
    View para um Candidato se aplicar a uma vaga.
    """
    if request.user.tipo_usuario != "candidato":
        messages.error(request, "Apenas candidatos podem se candidatar a vagas.")
        return redirect("home_recrutador")

    if request.method == "POST":
        try:
            vaga = get_object_or_404(Vaga, id=vaga_id, status=True)
            candidato = request.user.candidato

            Candidatura.objects.create(candidato=candidato, vaga=vaga, status="Enviada")
            messages.success(request, "Candidatura enviada com sucesso! Boa sorte.")

        except IntegrityError:
            messages.warning(request, "Você já se candidatou para esta vaga.")

        except Candidato.DoesNotExist:
            messages.error(
                request, "Você não possui um perfil de candidato para se candidatar."
            )

        except Exception as e:
            messages.error(request, f"Ocorreu um erro: {e}")

    return redirect("home_candidato")


# --- CORREÇÃO ---
# Removida a função duplicada e adicionado o login_required
@login_required
def perfil_empresa(request):
    """
    View para o Recrutador editar o perfil da empresa.
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(request, "Acesso negado.")
        return redirect("home_candidato")

    return render(request, "vagas/perfil_empresa.html")


@login_required
def ver_candidatos_vaga(request, vaga_id):
    """
    View para o Recrutador ver os candidatos que aplicaram
    para uma vaga específica, ordenados por score de matching.
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(request, "Acesso negado.")
        return redirect("home_candidato")

    vaga = get_object_or_404(Vaga, id=vaga_id)

    if vaga.recrutador.usuario != request.user:
        messages.error(request, "Você não tem permissão para ver esta página.")
        return redirect("home_recrutador")

    # --- CORREÇÃO BUG 0% ---
    # Adicionando de volta a otimização de performance
    candidaturas = (
        Candidatura.objects.filter(vaga=vaga)
        .select_related("candidato", "candidato__resumo_profissional")
        .prefetch_related(
            "candidato__skills", "candidato__experiencias", "candidato__formacoes"
        )
    )
    candidatos_com_score = []
    for candidatura in candidaturas:
        candidato = candidatura.candidato
        score = calcular_similaridade_tags(vaga, candidato)

        candidatos_com_score.append(
            {
                "candidato": candidato,
                "score": score,
                "data_aplicacao": candidatura.data_candidatura,
                "status": candidatura.status,
            }
        )

    candidatos_ordenados = sorted(
        candidatos_com_score, key=lambda item: item["score"], reverse=True
    )

    contexto = {"vaga": vaga, "candidatos_ordenados": candidatos_ordenados}

    return render(request, "vagas/ver_candidatos_vaga.html", contexto)


@login_required
def radar_de_talentos(request):
    """
    A nova tela de "Radar de Talentos" com a "Engine de IA".
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(request, "Acesso negado.")
        return redirect("home_candidato")

    try:
        recrutador = request.user.recrutador
    except Recrutador.DoesNotExist:
        messages.error(request, "Você não possui um perfil de recrutador associado.")
        return redirect("home_candidato")

    minhas_vagas = Vaga.objects.filter(recrutador=recrutador, status=True)
    candidatos_ordenados = []
    total_encontrados = 0
    vaga_selecionada_id = None

    if request.method == "POST":
        vaga_selecionada_id = request.POST.get("vaga_id")
        if vaga_selecionada_id:
            vaga = get_object_or_404(
                Vaga, id=vaga_selecionada_id, recrutador=recrutador
            )

            # --- CORREÇÃO BUG 0% ---
            # Adicionando de volta a otimização de performance
            todos_os_candidatos = (
                Candidato.objects.all()
                .select_related("usuario", "resumo_profissional")
                .prefetch_related("skills", "experiencias", "formacoes")
            )

            candidatos_com_score = []
            for candidato in todos_os_candidatos:
                score = calcular_similaridade_tags(vaga, candidato)

                if score > 20:
                    candidatos_com_score.append(
                        {"candidato": candidato, "score": score}
                    )

            candidatos_ordenados = sorted(
                candidatos_com_score, key=lambda item: item["score"], reverse=True
            )
            total_encontrados = len(candidatos_ordenados)
            vaga_selecionada_id = int(vaga_selecionada_id)

    contexto = {
        "minhas_vagas": minhas_vagas,
        "candidatos_ordenados": candidatos_ordenados,
        "total_encontrados": total_encontrados,
        "vaga_selecionada_id": vaga_selecionada_id,
    }

    return render(request, "vagas/radar_de_talentos.html", contexto)


@login_required
def planos_empresa(request):
    """
    View para a página de planos da empresa.
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(request, "Acesso negado.")
        return redirect("home_candidato")

    # --- CORREÇÃO ---
    # O caminho do template precisa do prefixo da pasta 'vagas/'
    return render(request, "vagas/planos_empresa.html")


# --- CORREÇÃO ---
# Adicionando de volta a view 'painel_admin' que estava faltando
@login_required
def painel_admin(request):
    """
    Painel administrativo com BUSCA e ESTATÍSTICAS reais.
    """
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Acesso negado.")
        return redirect('landing_page')

    # --- LÓGICA DE BUSCA ---
    query = request.GET.get('q') # Pega o termo da barra de pesquisa
    
    candidatos = Candidato.objects.all().order_by('-usuario__date_joined')
    empresas = Empresa.objects.all().order_by('-id')

    if query:
        # Filtra Candidatos (Nome ou Email)
        candidatos = candidatos.filter(
            Q(usuario__first_name__icontains=query) | 
            Q(usuario__email__icontains=query)
        )
        # Filtra Empresas (Nome ou CNPJ)
        empresas = empresas.filter(
            Q(nome__icontains=query) | 
            Q(cnpj__icontains=query)
        )
    # -----------------------

    # Estatísticas (Mantidas)
    um_mes_atras = timezone.now() - datetime.timedelta(days=30)
    contexto = {
        'nome_admin': request.user.first_name or request.user.username,
        'stat_novos_candidatos': Candidato.objects.filter(usuario__date_joined__gte=um_mes_atras).count(),
        'stat_novas_empresas': Empresa.objects.filter(id__in=Recrutador.objects.filter(usuario__date_joined__gte=um_mes_atras).values_list('empresa_id', flat=True)).count(),
        'stat_vagas_ativas': Vaga.objects.filter(status=True).count(),
        'stat_novas_candidaturas': Candidatura.objects.filter(data_candidatura__gte=um_mes_atras).count(),
        
        # Listas (agora filtráveis)
        'lista_candidatos': candidatos[:20], # Limita a 20 pra não travar
        'lista_empresas': empresas[:20],
        
        # Termo de busca (para manter no input)
        'busca_atual': query or ''
    }

    return render(request, "vagas/painel_admin.html", contexto)

@login_required
def toggle_status_usuario(request, user_id):
    """
    Ativa ou Desativa (Bane) um usuário.
    """
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Sem permissão.")
        return redirect('painel_admin')
        
    usuario = get_object_or_404(Usuario, id=user_id)
    
    # Não permitir que o admin se auto-bane
    if usuario == request.user:
        messages.error(request, "Você não pode desativar sua própria conta.")
        return redirect('painel_admin')

    # Inverte o status (Se tá ativo, desativa. Se tá inativo, ativa)
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    status_msg = "ativado" if usuario.is_active else "desativado"
    messages.success(request, f"Usuário {usuario.email} foi {status_msg} com sucesso.")
    
    return redirect('painel_admin')


def politica_privacidade(request):
    """
    Renderiza a página de Política de Privacidade.
    """
    return render(request, "vagas/politica_de_privacidade.html")

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
    
    # Processar Avaliação (POST) - SÓ PARA CANDIDATOS
    if request.method == 'POST':
        if request.user.tipo_usuario == 'candidato':
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
        else:
            messages.error(request, 'Apenas candidatos podem avaliar empresas.')
            
        return redirect('ver_empresa', empresa_id=empresa.id)

    # Dados para exibição
    avaliacoes = empresa.avaliacoes.all().order_by('-data')
    media = avaliacoes.aggregate(Avg('nota'))['nota__avg']
    
    # Verifica se o usuário JÁ avaliou (SE FOR CANDIDATO)
    minha_avaliacao = None
    if request.user.tipo_usuario == 'candidato':
        try:
            minha_avaliacao = avaliacoes.filter(candidato=request.user.candidato).first()
        except:
            pass 

    contexto = {
        'empresa': empresa,
        'vagas_abertas': Vaga.objects.filter(empresa=empresa, status=True),
        'avaliacoes': avaliacoes,
        'media_nota': round(media, 1) if media else "N/A",
        'minha_avaliacao': minha_avaliacao
    }
    # CORREÇÃO: Estava renderizando painel_admin.html errado aqui
    return render(request, 'vagas/ver_empresa.html', contexto)


@login_required
def confirmar_plano(request):
    """
    Processa a escolha do plano com LOGS DE DEPURAÇÃO.
    """
    print("\n--- INÍCIO CHECKOUT PLANO ---") # Log

    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, "Acesso negado.")
        return redirect('home_candidato')

    if request.method == 'POST':
        plano_selecionado = request.POST.get("plano") 
        print(f"1. Plano recebido do formulário: '{plano_selecionado}'") # Log
        
        planos_nomes = {
            "basico": "Plano Básico",
            "intermediario": "Plano Intermediário",
            "premium": "Plano Premium"
        }
        
        if not plano_selecionado or plano_selecionado not in planos_nomes:
            print("ERRO: Plano inválido ou vazio.") # Log
            messages.error(request, "Selecione um plano válido clicando em um dos cards.")
            return redirect("planos_empresa")
        
        recrutador = request.user.recrutador
        empresa = recrutador.empresa
        print(f"2. Empresa: {empresa.nome} | Plano Atual: {empresa.plano_assinado}") # Log

        # Regra de Downgrade
        if plano_selecionado == 'basico':
            vagas_ativas = Vaga.objects.filter(empresa=empresa, status=True).count()
            print(f"3. Verificando Downgrade. Vagas Ativas: {vagas_ativas}") # Log
            
            if vagas_ativas > 1:
                print("ERRO: Bloqueado por excesso de vagas.") # Log
                messages.error(
                    request, 
                    f"🚫 Não é possível mudar para o Básico: você tem {vagas_ativas} vagas abertas (limite 1). Encerre vagas antes."
                )
                return redirect("planos_empresa")

        # Salvar
        empresa.plano_assinado = plano_selecionado  
        empresa.save()
        print(f"4. SUCESSO! Plano alterado para {plano_selecionado}") # Log

        nome_plano = planos_nomes[plano_selecionado]
        messages.success(request, f"🎉 Plano alterado para **{nome_plano}**!")
        return redirect("home_recrutador")

    return redirect("planos_empresa")
    
    return render(request, 'vagas/painel_admin.html', contexto)

# Arquivo: apps/vagas/views.py (substituir a função existente)

# Arquivo: apps/vagas/views.py

@login_required
def confirmar_plano(request):
    """
    Processa a escolha do plano pelo Recrutador.
    INCLUI VALIDAÇÃO DE DOWNGRADE: Impede voltar para o Básico se tiver > 1 vaga.
    """
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, "Apenas recrutadores podem escolher planos.")
        return redirect('home_candidato')

    # Renomeando a variável para clareza
    plano_selecionado = request.POST.get("plano") 

    # Dicionário para traduzir o valor técnico para o nome completo
    planos_nomes = {
        "basico": "Plano Básico",
        "intermediario": "Plano Intermediário",
        "premium": "Plano Premium"
    }
    
    # 1. Validação básica de existência do plano
    if plano_selecionado not in planos_nomes:
        messages.error(request, "Selecione um plano válido antes de confirmar.")
        return redirect("planos_empresa")
    
    recrutador = request.user.recrutador
    empresa = recrutador.empresa

    # --- 2. NOVA REGRA DE BLOQUEIO (DOWNGRADE) ---
    # Se a empresa tentar mudar para o Básico...
    if plano_selecionado == 'basico':
        # Contamos quantas vagas abertas ela tem hoje
        vagas_ativas = Vaga.objects.filter(empresa=empresa, status=True).count()
        
        # Se tiver mais de 1 vaga, impedimos a troca!
        if vagas_ativas > 1:
            messages.error(
                request, 
                f"🚫 Não é possível mudar para o Plano Básico pois você tem {vagas_ativas} vagas abertas. "
                "O limite é de 1 vaga. Encerre as vagas excedentes primeiro."
            )
            return redirect("planos_empresa")
    # ---------------------------------------------

    # 3. Se passou pela validação, salva o novo plano
    empresa.plano_assinado = plano_selecionado  
    empresa.save()

    nome_plano = planos_nomes[plano_selecionado]
    messages.success(request, f"🎉 Parabéns! Sua empresa agora está utilizando o **{nome_plano}**.")

    return redirect("home_recrutador")

@login_required
def ajax_analise_ia_perfil(request):
    """
    Endpoint que recebe o pedido do Candidato e chama o Gemini.
    """
    if request.method == "POST":
        try:
            candidato = request.user.candidato
            
            # 1. Pega todo o texto do perfil (Resumo + XP + Skills)
            texto_completo = get_texto_candidato(candidato)
            
            # 2. Validação simples para não gastar IA à toa
            if len(texto_completo) < 50:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Seu perfil está muito vazio! Preencha Resumo e Experiências antes de pedir ajuda à IA.'
                })

            # 3. Chama o Gemini
            dicas_html = gerar_dicas_perfil(texto_completo)
            
            return JsonResponse({'status': 'success', 'dicas': dicas_html})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Método inválido'})