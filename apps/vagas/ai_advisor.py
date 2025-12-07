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

    prompt = f"""
    Aja como um recrutador sênior. Analise o perfil abaixo e dê 3 dicas curtas e diretas.
    SAÍDA OBRIGATÓRIA: Apenas código HTML cru (tags <ul>, <li>, <strong>).
    NÃO use crases de markdown (```html). NÃO coloque introdução.
    
    Perfil: "{perfil_texto}"
    """

    try:
        # --- MUDANÇA: BUSCA DINÂMICA DE MODELOS ---
        print("🔍 Buscando modelos disponíveis na API...")
        
        # Lista todos os modelos que a sua chave tem acesso
        modelos_disponiveis = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Prioriza modelos 'gemini'
                if 'gemini' in m.name:
                    modelos_disponiveis.append(m.name)
        
        # Ordena para tentar os mais recentes primeiro (opcional, mas bom)
        modelos_disponiveis.sort(reverse=True) 
        
        print(f"📋 Modelos encontrados: {modelos_disponiveis}")

        if not modelos_disponiveis:
            return "<ul><li>Nenhum modelo de IA disponível para esta chave.</li></ul>"

        # Tenta um por um da lista real que o Google devolveu
        for modelo_nome in modelos_disponiveis:
            try:
                print(f"Tentando usar: {modelo_nome}...")
                model = genai.GenerativeModel(modelo_nome)
                response = model.generate_content(prompt)
                texto_limpo = response.text
                texto_limpo = texto_limpo.replace("```html", "").replace("```", "")
                return texto_limpo
            except Exception as e:
                print(f"❌ Erro no modelo {modelo_nome}: {e}")
                continue
    
    except Exception as e:
        print(f"Erro fatal ao listar modelos: {e}")
        return f"<ul><li>Erro de conexão com a IA: {e}</li></ul>"
            
    return "<ul><li>IA temporariamente indisponível (Cota excedida ou erro interno).</li></ul>"