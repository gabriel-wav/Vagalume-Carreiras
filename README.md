# 💡 Vagalume Carreiras  
**"Illuminating careers, connecting futures."**

![Vagalume Banner](https://img.shields.io/badge/Vagalume-Carreiras-BEF264?style=for-the-badge&logoColor=0D1B2A&labelColor=0D1B2A)
![Status](https://img.shields.io/badge/Status-Completed-success?style=flat-square)
![Version](https://img.shields.io/badge/Version-1.0.0-blue?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.0+-092E20?style=flat&logo=django&logoColor=white)


**LIVE DEMO:** https://vagalume-carreiras-production.up.railway.app/

**Vagalume Carreiras** is an intelligent recruitment and selection platform developed as a **Final Undergraduate Thesis (TCC)**.  
Unlike traditional job portals, the system uses **Generative Artificial Intelligence (Google Gemini)** and **Semantic Matching** to connect ideal candidates to the right job openings, while also offering **financial management** and **career guidance** tools.

---

## 🚀 Key Features

### 👤 For Candidates
- **Web & PDF Resume:** Creation of a detailed profile (Summary, Experience, Education, Skills) and attachment for a PDF resume.
- **Vagalume AI Advisor:** AI-powered profile analysis (Google Gemini) with personalized tips to improve your resume and increase your chances of being hired.
- **Simplified Application:** Apply to job openings with just one click.
- **Financial Education:** Exclusive module with a net salary calculator (Brazilian CLT regime) and budgeting tips for newcomers to the job market.
- **Secure Recovery:** Password recovery via **Email** or **SMS** (Twilio integration).

### 🏢 For Companies (Recruiters)
- **Job Management:** Full CRUD for job listings with status control (Open/Closed).
- **Talent Radar (AI - Matching):**  
  **Semantic Matching** algorithm (sentence-transformers) that scans the database and ranks candidates by compatibility percentage, even without a prior application.
- **Subscription Plans:** Basic, Intermediate, and Premium, with job listing limits and access to AI features.
- **Admin Dashboard:** Overview of metrics, candidates, and employer brand management.

---

## 🛠️ Tech Stack

### Backend & Core
- **Python**
- **Django Framework**
- **PostgreSQL**
- **Django REST Framework**

### Artificial Intelligence & Data
- 🤖 **Google Gemini (Generative AI)** – Profile analysis and career guidance  
- 🧠 **Sentence-Transformers (Torch)** – Embedding generation and semantic similarity  
- 📊 **Scikit-Learn & NumPy** – Vector and numerical processing  

### Frontend
- 🎨 **HTML5, CSS3 and JavaScript**
- **Jinja2 (Django Templates)**
- **Dark Mode** theme with Neon accents (**#BEF264**)

### External Services
- 📧 **SMTP (Gmail)** – Email delivery for password recovery
- 📱 **Twilio** – SMS delivery for password recovery

---

## ⚙️ Local Installation & Setup

### 1. Prerequisites
- Python **3.10+**
- PostgreSQL installed and running
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/pedroH901/Vagalume-Carreiras.git
cd vagalume-carreiras
```

### 3. Create a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / Mac
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```
This will install packages such as PyTorch, Django, Google GenAI, and others.

### 5. Configure Environment Variables
Create a .env file in the project root:
```bash
# Database
DB_NAME=vagalume_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Google AI (Gemini)
GOOGLE_API_KEY=your_key_here

# Email
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Twilio (Optional)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=your_number
```

### 6. Migrations & Database
Create the database in PostgreSQL and run:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create a Superuser
```bash
python manage.py createsuperuser
```

### 8. Run the Server
```bash
python manage.py runserver
```
Access:
👉 http://127.0.0.1:8000/

---

## 🧠 How does the AI (Matching) work?

The differentiator of **Vagalume Carreiras** lies in the **Talent Radar**:

1. The system converts:
   - The candidate's **Summary + Experience + Skills**  
     into mathematical vectors (*embeddings*) using pre-trained models  
     (`distiluse-base-multilingual-cased-v1`).

2. The same process is applied to the job listing:
   - The job's **Title + Description + Requirements**.

3. A **Cosine Similarity Calculation** is performed between the vectors.

4. The system generates a **Match Score (0 to 100%)** that understands **semantic context**  
   (e.g.: `"Dev Frontend" ≈ "React Developer"`), without relying solely on exact keyword matches.

---

## 👥 Authors (TCC Team)

- **Pedro Henrique** – Full Stack Developer  
- **Danilo** – Backend Developer  
- **Gabriel** – Full Stack Developer  
- **Antonio** – Database Specialist

---

## 📄 License

This project is for **educational and academic use**.  
Unauthorized distribution and copying **are prohibited**.

---

<p align="center">
Made with 💚 and lots of coffee by <strong>Team Vagalume</strong>.
</p>
