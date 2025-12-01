import google.generativeai as genai

# --- CONFIGURAÇÃO ---
# Coloque sua chave aqui para testar
API_KEY = "AIzaSyDRCM04_8yh5VcTTqTt3-wopvgkYiUyA-Q" 

try:
    genai.configure(api_key=API_KEY)
    
    print(f"Listando modelos disponíveis para a chave configurada...\n")
    
    encontrou_algum = False
    for m in genai.list_models():
        # Filtra apenas modelos que geram texto (chat)
        if 'generateContent' in m.supported_generation_methods:
            print(f"Nome: {m.name}")
            print(f"Display: {m.display_name}")
            print("-" * 30)
            encontrou_algum = True
            
    if not encontrou_algum:
        print("Nenhum modelo de geração de texto encontrado para essa chave.")
        
except Exception as e:
    print(f"Erro ao conectar: {e}")