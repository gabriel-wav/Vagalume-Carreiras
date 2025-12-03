# 💡 Vagalume Carreiras  
**"Iluminando carreiras, conectando futuros."**

![Vagalume Banner](https://img.shields.io/badge/Vagalume-Carreiras-BEF264?style=for-the-badge&logoColor=0D1B2A&labelColor=0D1B2A)
![Status](https://img.shields.io/badge/Status-Concluído-success?style=flat-square)
![Versão](https://img.shields.io/badge/Versão-1.0.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=flat&logo=django&logoColor=white)

O **Vagalume Carreiras** é uma plataforma de recrutamento e seleção inteligente desenvolvida como **Trabalho de Conclusão de Curso (TCC)**.  
Diferente de portais tradicionais, o sistema utiliza **Inteligência Artificial Generativa (Google Gemini)** e **Matching Semântico** para conectar os candidatos ideais às vagas certas, além de oferecer ferramentas de **gestão financeira** e **orientação de carreira**.

---

## 🚀 Funcionalidades Principais

### 👤 Para Candidatos
- **Currículo Web & PDF:** Criação de perfil detalhado (Resumo, Experiência, Formação, Skills) e anexo para currículo em PDF.
- **Vagalume AI Advisor:** Análise de perfil por IA (Google Gemini) com dicas personalizadas para melhorar o currículo e aumentar as chances de contratação.
- **Candidatura Simplificada:** Aplicação para vagas com apenas um clique.
- **Educação Financeira:** Módulo exclusivo com calculadora de salário líquido (CLT) e dicas de orçamento para iniciantes no mercado.
- **Recuperação Segura:** Recuperação de senha via **E-mail** ou **SMS** (integração com Twilio).

### 🏢 Para Empresas (Recrutadores)
- **Gestão de Vagas:** CRUD completo de vagas com controle de status (Aberta/Fechada).
- **Radar de Talentos (IA - Matching):**  
  Algoritmo de **Semantic Matching** (sentence-transformers) que varre o banco de dados e ranqueia candidatos por compatibilidade percentual, mesmo sem candidatura prévia.
- **Planos de Assinatura:** Básico, Intermediário e Premium, com limites de vagas e acesso a funcionalidades de IA.
- **Dashboard Administrativo:** Visão geral de métricas, candidatos e gestão da marca empregadora.

---

## 🛠️ Stack Tecnológica

### Backend & Core
- **Python**
- **Django Framework**
- **PostgreSQL**
- **Django REST Framework**

### Inteligência Artificial & Dados
- 🤖 **Google Gemini (Generative AI)** – Análise de perfis e orientação de carreira  
- 🧠 **Sentence-Transformers (Torch)** – Geração de embeddings e similaridade semântica  
- 📊 **Scikit-Learn & NumPy** – Processamento vetorial e numérico  

### Frontend
- 🎨 **HTML5, CSS3 e JavaScript**
- **Jinja2 (Django Templates)**
- Tema **Dark Mode** com acentos Neon (**#BEF264**)

### Serviços Externos
- 📧 **SMTP (Gmail)** – Envio de e-mails para recuperação de senha
- 📱 **Twilio** – Envio de SMS para recuperação de senha

---

## ⚙️ Instalação e Configuração Local

### 1. Pré-requisitos
- Python **3.10+**
- PostgreSQL instalado e em execução
- Git

### 2. Clonar o Repositório
```bash
git clone https://github.com/pedroH901/Vagalume-Carreiras.git
cd vagalume-carreiras
```

### 3. Criar Ambiente Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar Dependências
```bash
pip install -r requirements.txt
```
Isso instalará pacotes como PyTorch, Django, Google GenAI, entre outros.

### 5. Configurar Variáveis de Ambiente
Crie um arquivo .env na raiz do projeto:
```bash
# Banco de Dados
DB_NAME=vagalume_db
DB_USER=postgres
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432

# Google AI (Gemini)
GOOGLE_API_KEY=sua_chave_aqui

# Email
EMAIL_HOST_USER=seu_email@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app

# Twilio (Opcional)
TWILIO_ACCOUNT_SID=seu_sid
TWILIO_AUTH_TOKEN=seu_token
TWILIO_PHONE_NUMBER=seu_numero
```

### 6. Migrações e Base de Dados
Crie o banco no PostgreSQL e execute:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Criar Superusuário
```bash
python manage.py createsuperuser
```

### 8. Executar o Servidor
```bash
python manage.py runserver
```
Acesse:
👉 http://127.0.0.1:8000/

---

## 🧠 Como funciona a IA (Matching)?

O diferencial do **Vagalume Carreiras** está no **Radar de Talentos**:

1. O sistema converte:
   - **Resumo + Experiências + Skills** do candidato  
     em vetores matemáticos (*embeddings*) usando modelos pré-treinados  
     (`distiluse-base-multilingual-cased-v1`).

2. O mesmo processo é aplicado para a vaga:
   - **Título + Descrição + Requisitos** da vaga.

3. É realizado o **Cálculo de Similaridade de Cosseno** entre os vetores.

4. O sistema gera um **Match Score (0 a 100%)** que entende o **contexto semântico**  
   (ex.: `"Dev Frontend" ≈ "React Developer"`), e não depende apenas de palavras-chave exatas.

---

## 👥 Autores (Equipe TCC)

- **Pedro Henrique** – Full Stack Developer  
- **Danilo** – Backend Developer  
- **Gabriel** – Full Stack Developer  
- **Antonio** – Database Specialist

---

## 📄 Licença

Este projeto é de **uso educacional e acadêmico**.  
Distribuição e cópia **não autorizadas são proibidas**.

---

<p align="center">
Feito com 💚 e muito café por <strong>Time Vagalume</strong>.
</p>

