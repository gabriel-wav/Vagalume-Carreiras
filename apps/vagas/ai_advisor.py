# apps/vagas/ai_advisor.py
import google.generativeai as genai
import os
from django.conf import settings

# --- CONFIGURAÇÃO DA CHAVE ---
# Você pode colocar a chave direto aqui para testar (não recomendado para produção)
# Ou usar: os.environ.get("GOOGLE_API_KEY")
API_KEY = "AIzaSyDRCM04_8yh5VcTTqTt3-wopvgkYiUyA-Q" 

def configurar_ia():
    try:
        genai.configure(api_key=API_KEY)
        return True
    except Exception as e:
        print(f"Erro ao configurar IA: {e}")
        return False

def gerar_dicas_perfil(perfil_texto):
    """
    Recebe o texto do perfil do candidato e retorna dicas de melhoria em HTML.
    """
    if not configurar_ia():
        return "<ul><li>Erro de conexão com a IA. Verifique a API Key.</li></ul>"

    # Modelo mais recente e estável
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    Aja como um recrutador sênior de tecnologia e 'Career Coach'.
    Analise o seguinte perfil de candidato e me dê 3 dicas práticas, diretas e construtivas
    para ele melhorar o perfil e conseguir mais entrevistas.
    
    Foque em: Palavras-chave, clareza, impacto e tecnologias faltantes (se aplicável).
    
    Perfil do Candidato:
    "{perfil_texto}"
    
    IMPORTANTE: Sua resposta deve ser APENAS uma lista HTML (<ul> com <li>), sem tags <html>, <head> ou markdown ```html.
    Seja amigável mas profissional.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text # O Gemini vai devolver o HTML pronto
    except Exception as e:
        return f"<ul><li>O Vagalume AI está sobrecarregado. Erro: {e}</li></ul>"