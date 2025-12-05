import google.generativeai as genai
import os
from django.conf import settings
from google.api_core import exceptions

def configurar_ia():
    try:
        # CORREÇÃO CRÍTICA: Pega a chave do settings (que vem do Railway)
        api_key = settings.GOOGLE_API_KEY
        
        if not api_key:
            print("❌ ERRO: GOOGLE_API_KEY não encontrada no settings.")
            return False
            
        genai.configure(api_key=api_key)
        return True
    except Exception as e:
        print(f"❌ Erro ao configurar IA: {e}")
        return False

def gerar_dicas_perfil(perfil_texto):
    if not configurar_ia():
        return "<ul><li>Erro de configuração da IA (Chave API não detectada).</li></ul>"

    # Lista de modelos (Prioridade: Flash 2.0 > Flash 1.5 > Pro)
    modelos_para_tentar = [
        'gemini-2.0-flash',
        'gemini-2.0-flash-lite',
        'gemini-1.5-flash',
    ]

    prompt = f"""
    Aja como um recrutador sênior de tecnologia e 'Career Coach'.
    Analise o seguinte perfil de candidato e me dê 3 dicas práticas, diretas e construtivas.
    
    Foque em: Palavras-chave, clareza, impacto e tecnologias faltantes.
    
    Perfil do Candidato:
    "{perfil_texto}"
    
    IMPORTANTE:
    1. Sua resposta deve ser APENAS uma lista HTML (<ul> com <li>).
    2. Não use tags <html>, <head> ou markdown.
    3. Destaque o ponto principal de cada dica em negrito (<strong>).
    """

    for nome_modelo in modelos_para_tentar:
        try:
            print(f"🤖 Tentando modelo: {nome_modelo}...")
            model = genai.GenerativeModel(nome_modelo)
            
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    candidate_count=1,
                    max_output_tokens=500,
                    temperature=0.7
                )
            )
            return response.text 
            
        except exceptions.ResourceExhausted:
            print(f"⚠️ Cota excedida para {nome_modelo}. Tentando próximo...")
            continue 
        except Exception as e:
            print(f"❌ Erro no modelo {nome_modelo}: {e}")
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            continue
            
    return "<ul><li>O Vagalume AI está temporariamente indisponível. Tente novamente em 1 minuto.</li></ul>"