from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from apps.usuarios.models import Candidato, Resumo_Profissional, Skill, Experiencia
from apps.vagas.models import Vaga

def _get_texto_candidato(candidato):
    """
    Junta todos os campos de texto relevantes de um candidato em um "documento".
    """
    texto = ""

    # 1. Pega o Resumo
    try:
        texto += candidato.resumo_profissional.texto + " "
    except Resumo_Profissional.DoesNotExist:
        pass

    # 2. Pega as Skills
    skills = " ".join([skill.nome for skill in candidato.skills.all()])
    texto += skills + " "

    # 3. Pega os cargos das Experiências
    cargos = " ".join([exp.cargo for exp in candidato.experiencias.all()])
    texto += cargos

    return texto

def _get_texto_vaga(vaga):
    """
    Junta todos os campos de texto relevantes de uma vaga em um "documento".
    """
    return f"{vaga.titulo} {vaga.descricao} {vaga.requisitos}"

def calcular_similaridade(vaga, candidato):
    """
    Calcula o score de "match" (0 a 100) entre uma vaga e um candidato.
    """
    texto_vaga = _get_texto_vaga(vaga)
    texto_candidato = _get_texto_candidato(candidato)

    # Se o candidato não tiver perfil, o match é 0
    if not texto_candidato.strip():
        return 0

    # Lista de documentos para o TF-IDF
    documentos = [texto_vaga, texto_candidato]

    # Processa os textos
    tfidf_vectorizer = TfidfVectorizer(stop_words='english') # (Pode add 'portuguese' depois)
    tfidf_matrix = tfidf_vectorizer.fit_transform(documentos)

    # Calcula a similaridade
    similaridade = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])

    # Converte para porcentagem (0 a 100)
    score = round(similaridade[0][0] * 100, 2)

    return score