# Arquivo: apps/matching/engine.py (VERSÃO "IA")

# 1. Importe as bibliotecas de IA
from sentence_transformers import SentenceTransformer, util
from apps.usuarios.models import Candidato
from apps.vagas.models import Vaga

# 2. Carregue o modelo de IA (só uma vez, quando o app inicia)
#    Vamos usar um modelo pré-treinado para o português.
try:
    # Este é um modelo leve e bom para o português
    model = SentenceTransformer('distiluse-base-multilingual-cased-v1')
except Exception as e:
    # Se der erro no carregamento, você saberá
    print(f"Erro ao carregar o modelo de IA: {e}")
    model = None

def get_texto_candidato(candidato: Candidato) -> str:
    """
    Junta todo o perfil de texto do candidato em uma única string.
    """
    textos = []
    
    # Pega o Resumo Profissional
    if hasattr(candidato, 'resumo_profissional'):
        textos.append(candidato.resumo_profissional.texto)
        
    # Pega as Skills
    skills = [skill.nome for skill in candidato.skills.all()]
    if skills:
        textos.append("Habilidades: " + ", ".join(skills))
        
    # Pega as Experiências
    for exp in candidato.experiencias.all():
        textos.append(f"Experiência como {exp.cargo} em {exp.empresa}: {exp.descricao}")
        
    # Pega as Formações
    for formacao in candidato.formacoes.all():
        textos.append(f"Formação em {formacao.nome_formacao} na {formacao.nome_instituicao}")
        
    return ". ".join(textos)

def get_texto_vaga(vaga: Vaga) -> str:
    """
    Junta todo o texto da vaga em uma única string.
    """
    textos = [
        vaga.titulo,
        vaga.descricao,
        "Requisitos: " + vaga.requisitos
    ]
    return ". ".join(textos)

def calcular_similaridade_tags(vaga, candidato):
    """
    A "Engine" de IA!
    Calcula a "Similaridade de Cosseno" entre os vetores da Vaga e do Candidato.
    
    (Mantivemos o nome da função para não quebrar suas views!)
    """
    if model is None:
        print("Modelo de IA não carregado. Retornando 0.")
        return 0

    try:
        # 1. Converte os perfis em texto puro
        texto_vaga = get_texto_vaga(vaga)
        texto_candidato = get_texto_candidato(candidato)

        if not texto_vaga or not texto_candidato:
            return 0 # Não dá para comparar textos vazios

        # 2. Codifica os textos em Vetores (Embeddings) - A "IA" ACONTECE AQUI!
        embedding_vaga = model.encode(texto_vaga, convert_to_tensor=True)
        embedding_candidato = model.encode(texto_candidato, convert_to_tensor=True)

        # 3. Calcula a Similaridade de Cosseno
        # Isso retorna um score, por exemplo, 0.85
        cosine_scores = util.cos_sim(embedding_vaga, embedding_candidato)
        score = cosine_scores.item() # Pega o valor numérico

        # 4. Converte para porcentagem (de 0 a 100)
        return round(max(score, 0) * 100)

    except Exception as e:
        print(f"Erro ao calcular similaridade para vaga {vaga.id} e candidato {candidato.pk}: {e}")
        return 0