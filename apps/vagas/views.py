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
)
from django.db.models import Avg
from apps.usuarios.models import AvaliacaoEmpresa
from django.db.models import Count


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

@login_required
def criar_vaga(request):
    """
    View para um Recrutador criar uma nova vaga.
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(
            request, "Acesso negado. Esta página é apenas para recrutadores."
        )
        return redirect("home_candidato")

    recrutador_logado = get_object_or_404(Recrutador, usuario=request.user)
    empresa = recrutador_logado.empresa
    
    # --- LÓGICA DE RESTRIÇÃO DE PLANO ---
    plano_atual = empresa.plano_assinado
    
    # Contabiliza APENAS vagas ativas (status=True) publicadas por esta empresa
    vagas_ativas_count = Vaga.objects.filter(recrutador__empresa=empresa, status=True).count()

    # Verifica se é Plano Básico E se já atingiu o limite de 1 vaga ativa
    if plano_atual == 'basico' and vagas_ativas_count >= 1:
        messages.error(
            request, 
            'Seu **Plano Básico** permite apenas **1 vaga ativa**. Para publicar mais, altere para o Plano Intermediário ou Premium.'
        )
        return redirect('planos_empresa') # Redireciona para a página de planos
    # --- FIM LÓGICA DE RESTRIÇÃO DE PLANO ---

    if request.method == "POST":
        form = VagaForm(request.POST, empresa=recrutador_logado.empresa)

        if form.is_valid():
            vaga = form.save(commit=False, recrutador=recrutador_logado)
            vaga.save()
            messages.success(request, "Vaga criada com sucesso!")
            return redirect("home_recrutador")
    else:
        form = VagaForm(empresa=recrutador_logado.empresa)

    return render(request, "vagas/criar_vaga.html", {"form": form})


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
    Painel do Recrutador, lista as vagas criadas por ele. (R do CRUD)
    Adiciona o plano atual da empresa ao contexto.
    """
    if request.user.tipo_usuario != "recrutador":
        messages.error(request, "Acesso negado.")
        return redirect("home_candidato")

    try:
        recrutador = request.user.recrutador
        # 1. Obter a Empresa do Recrutador
        empresa = recrutador.empresa

        # 2. Dicionário para formatar o nome do plano
        planos_nomes = {
            "basico": "Plano Básico",
            "intermediario": "Plano Intermediário",
            "premium": "Plano Premium"
        }

        plano_atual_slug = empresa.plano_assinado 
        # Obtém o nome amigável. Usa 'Nenhum Plano' como fallback
        plano_atual_nome = planos_nomes.get(plano_atual_slug, "Nenhum Plano") 

    except Recrutador.DoesNotExist:
        messages.error(request, "Você não possui um perfil de recrutador associado.")
        return redirect("home_candidato")

    minhas_vagas = Vaga.objects.filter(recrutador=recrutador)
    
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
    View para o novo painel de administrador customizado.
    Valida se o usuário é um 'superuser' ou 'staff'.
    """

    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, "Acesso negado. Esta página é restrita.")
        if request.user.tipo_usuario == "candidato":
            return redirect("home_candidato")
        elif request.user.tipo_usuario == "recrutador":
            return redirect("home_recrutador")
        else:
            return redirect("landing_page")  # Fallback

    um_mes_atras = timezone.now() - datetime.timedelta(days=30)

    novos_candidatos = Candidato.objects.filter(
        usuario__date_joined__gte=um_mes_atras
    ).count()
    novas_empresas = Empresa.objects.filter(
        id__in=Recrutador.objects.filter(
            usuario__date_joined__gte=um_mes_atras
        ).values_list("empresa_id", flat=True)
    ).count()
    vagas_ativas = Vaga.objects.filter(status=True).count()
    novas_candidaturas = Candidatura.objects.filter(
        data_candidatura__gte=um_mes_atras
    ).count()

    ultimos_candidatos = Candidato.objects.all().order_by("-usuario__date_joined")[:10]
    ultimas_empresas = Empresa.objects.all().order_by("-id")[:10]

    candidatos_recentes = Candidato.objects.all().order_by("-usuario__date_joined")[:5]
    empresas_recentes = Empresa.objects.all().order_by("-id")[:5]
    vagas_recentes = Vaga.objects.all().order_by("-data_publicacao")[:5]

    contexto = {
        "nome_admin": request.user.first_name or request.user.username,
        "stat_novos_candidatos": novos_candidatos,
        "stat_novas_empresas": novas_empresas,
        "stat_vagas_ativas": vagas_ativas,
        "stat_novas_candidaturas": novas_candidaturas,
        "lista_candidatos": ultimos_candidatos,
        "lista_empresas": ultimas_empresas,
        "atividades_candidatos": candidatos_recentes,
        "atividades_empresas": empresas_recentes,
        "atividades_vagas": vagas_recentes,
    }

    return render(request, "vagas/painel_admin.html", contexto)


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
            pass # Se der erro de perfil, ignora

    contexto = {
        'empresa': empresa,
        'vagas_abertas': Vaga.objects.filter(empresa=empresa, status=True),
        'avaliacoes': avaliacoes,
        'media_nota': round(media, 1) if media else "N/A",
        'minha_avaliacao': minha_avaliacao,
        'is_dono': False # Flag para mostrar botões de edição no futuro
    }
    
    return render(request, 'vagas/painel_admin.html', contexto)

# Arquivo: apps/vagas/views.py (substituir a função existente)

@login_required
def confirmar_plano(request):
    if request.user.tipo_usuario != 'recrutador':
        messages.error(request, "Apenas recrutadores podem escolher planos.")
        return redirect('home_candidato')

    # Renomeando a variável para clareza
    plano_selecionado = request.POST.get("plano") 

    # Dicionário para traduzir o valor técnico para o nome completo (NOVO)
    planos_nomes = {
        "basico": "Plano Básico",
        "intermediario": "Plano Intermediário",
        "premium": "Plano Premium"
    }
    
    # 1. Validação aprimorada (Substitui o bloco antigo)
    if plano_selecionado not in planos_nomes:
        messages.error(request, "Selecione um plano antes de confirmar.")
        return redirect("planos_empresa")
    
    # Obtém o nome amigável para a mensagem
    nome_plano = planos_nomes[plano_selecionado]

    recrutador = request.user.recrutador
    empresa = recrutador.empresa

    # 2. Salva o plano escolhido no modelo Empresa
    empresa.plano_assinado = plano_selecionado  
    empresa.save()

    # 3. Adiciona a mensagem de sucesso usando o nome amigável
    messages.success(request, f"🎉 Parabéns! Sua empresa agora está utilizando o **{nome_plano}**.")

    # 4. Redireciona para o painel do recrutador
    return redirect("home_recrutador")
