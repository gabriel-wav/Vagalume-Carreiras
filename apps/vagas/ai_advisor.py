import google.generativeai as genai
import os
from django.conf import settings
from google.api_core import exceptions

def configurar_ia():
    try:
        # LÊ DO SETTINGS.PY (CRUCIAL PARA O RAILWAY)
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
        return "<ul><li>Erro: Chave de API não configurada no painel.</li></ul>"

   # Colocamos o 1.5 Flash primeiro porque ele é o mais estável e tem mais cota
    modelos = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']

    prompt = f"""
    Aja como um recrutador sênior de tecnologia.
    Analise o perfil abaixo e dê 3 dicas práticas (HTML <li> com <strong> no título).
    Perfil: "{perfil_texto}"
    """

    for modelo in modelos:
        try:
            print(f"Tentando {modelo}...")
            model = genai.GenerativeModel(modelo)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            # AQUI ESTÁ A MUDANÇA: Vamos imprimir o erro real no log!
            print(f"❌ FALHA no modelo {modelo}: {str(e)}")
            continue
            
    return "<ul><li>IA temporariamente indisponível. Verifique os logs do servidor.</li></ul>"