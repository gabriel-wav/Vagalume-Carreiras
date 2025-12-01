import google.generativeai as genai
import os
from django.conf import settings
from google.api_core import exceptions

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
    Tenta vários modelos disponíveis para evitar erros de cota ou indisponibilidade.
    """
    if not configurar_ia():
        return "<ul><li>Erro de conexão com a IA. Verifique a API Key.</li></ul>"

    # Lista de modelos baseada na SUA lista disponível (do melhor para o mais leve)
    modelos_para_tentar = [
        'gemini-2.0-flash',          # 1. Tentativa Principal (Rápido e Inteligente)
        'gemini-2.0-flash-lite',     # 2. Fallback Leve (Ótimo para economizar cota)
        'gemini-2.0-pro-exp-02-05',  # 3. Fallback Potente (Se os Flash falharem)
    ]

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

    for nome_modelo in modelos_para_tentar:
        try:
            print(f"Tentando usar modelo: {nome_modelo}...") 
            model = genai.GenerativeModel(nome_modelo)
            
            # Configuração para resposta mais criativa e direta
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
            print(f"Cota excedida para {nome_modelo}. Tentando próximo...")
            continue # Pula para o próximo modelo da lista
            
        except Exception as e:
            print(f"Erro no modelo {nome_modelo}: {e}")
            # Se o erro for "not found" (caso o Google mude o nome), tenta o próximo
            if "404" in str(e) or "not found" in str(e).lower():
                continue
            # Se for outro erro grave, para por aqui
            continue

    # Se todos os modelos falharem
    return "<ul><li>O Vagalume AI está temporariamente sobrecarregado. Por favor, tente novamente em alguns instantes.</li></ul>"