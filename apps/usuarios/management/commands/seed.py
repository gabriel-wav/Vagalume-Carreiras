from django.core.management.base import BaseCommand
from apps.usuarios.models import Usuario, Candidato, Empresa, Recrutador, Skill, Experiencia, Resumo_Profissional
from apps.vagas.models import Vaga, Plano
import datetime
import random

class Command(BaseCommand):
    help = 'Popula o banco de dados com dados massivos de teste'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Iniciando Seed Robusto...')

        # 1. PLANOS
        planos = [
            {'chave': 'basico', 'nome': 'Básico', 'preco': 0.00, 'limite': 1},
            {'chave': 'intermediario', 'nome': 'Intermediário', 'preco': 150.00, 'limite': 10},
            {'chave': 'premium', 'nome': 'Premium', 'preco': 400.00, 'limite': 999},
        ]
        for p in planos:
            Plano.objects.get_or_create(nome_chave=p['chave'], defaults={'nome_exibicao': p['nome'], 'preco': p['preco'], 'limite_vagas': p['limite']})

        # 2. ADMIN
        if not Usuario.objects.filter(email='admin@vagalume.com').exists():
            Usuario.objects.create_superuser('admin@vagalume.com', 'admin@vagalume.com', 'admin', first_name='Super', last_name='Admin')

        # 3. EMPRESAS E RECRUTADORES (3 Empresas diferentes)
        empresas_data = [
            {'nome': 'Vagalume Tech', 'setor': 'Tecnologia', 'cnpj': '10000000000100', 'rec_nome': 'Chefe', 'rec_email': 'recrutador@vagalume.com'},
            {'nome': 'InovaSoft', 'setor': 'Tecnologia', 'cnpj': '20000000000100', 'rec_nome': 'Ana', 'rec_email': 'ana@inovasoft.com'},
            {'nome': 'Banco Futuro', 'setor': 'Financeiro', 'cnpj': '30000000000100', 'rec_nome': 'Carlos', 'rec_email': 'carlos@bancofuturo.com'},
        ]

        for emp in empresas_data:
            empresa, _ = Empresa.objects.get_or_create(
                cnpj=emp['cnpj'], 
                defaults={'nome': emp['nome'], 'setor': emp['setor'], 'telefone': '11999999999', 'plano_assinado': 'premium'}
            )
            
            if not Usuario.objects.filter(email=emp['rec_email']).exists():
                u = Usuario.objects.create_user(emp['rec_email'], emp['rec_email'], '123', first_name=emp['rec_nome'], last_name='Recrutador', tipo_usuario='recrutador')
                Recrutador.objects.create(usuario=u, empresa=empresa)
                
                # Criar vaga para essa empresa
                Vaga.objects.create(
                    empresa=empresa, recrutador=u.recrutador, titulo=f'Desenvolvedor em {emp["nome"]}',
                    area_atuacao='tecnologia', descricao=f'Vaga incrível na {emp["nome"]}.', requisitos='Python, Django',
                    tipo_contrato='CLT', localidade='São Paulo', faixa_salarial='R$ 5.000', status=True
                )

        # 4. CANDIDATOS (15 Perfis Variados)
        candidatos_data = [
            # NOME, HEADLINE, SKILLS (Hard), NIVEL
            ('João Python', 'Dev Python Junior', ['Python', 'Django', 'SQL'], 'Iniciante'),
            ('Maria Java', 'Engenheira de Software', ['Java', 'Spring', 'Docker'], 'Pleno'),
            ('Pedro Frontend', 'Dev React', ['JavaScript', 'React', 'CSS'], 'Júnior'),
            ('Lucas Dados', 'Cientista de Dados', ['Python', 'Pandas', 'Machine Learning'], 'Sênior'),
            ('Ana Design', 'UX/UI Designer', ['Figma', 'Adobe XD', 'Prototipagem'], 'Pleno'),
            ('Carla Tech', 'Dev Full Stack', ['Python', 'React', 'Node.js'], 'Sênior'),
            ('Marcos Ops', 'DevOps Engineer', ['AWS', 'Docker', 'Kubernetes'], 'Pleno'),
            ('Julia Mobile', 'Dev iOS', ['Swift', 'iOS', 'Xcode'], 'Júnior'),
            ('Bruno Back', 'Backend Developer', ['Go', 'Microservices', 'SQL'], 'Pleno'),
            ('Fernanda PM', 'Product Manager', ['Scrum', 'Jira', 'Liderança'], 'Sênior'),
            ('Rafael Sec', 'Analista de Segurança', ['Cybersecurity', 'Linux', 'Network'], 'Pleno'),
            ('Beatriz QA', 'QA Engineer', ['Selenium', 'Python', 'Testes'], 'Júnior'),
            ('Gustavo Cloud', 'Cloud Architect', ['Azure', 'Terraform', 'Python'], 'Sênior'),
            ('Larissa AI', 'Engenheira de IA', ['PyTorch', 'TensorFlow', 'NLP'], 'Pleno'),
            ('Roberto Legacy', 'Analista de Sistemas', ['Cobol', 'Java', 'SQL'], 'Sênior'),
        ]

        for i, (nome, headline, skills, nivel) in enumerate(candidatos_data):
            email = f'candidato{i+1}@teste.com'
            if not Usuario.objects.filter(email=email).exists():
                u = Usuario.objects.create_user(email, email, '123', first_name=nome.split()[0], last_name=nome.split()[1], tipo_usuario='candidato')
                c = Candidato.objects.create(usuario=u, cpf=f'111222333{i:02d}', headline=headline)
                
                # Resumo rico para IA
                Resumo_Profissional.objects.create(candidato=c, texto=f"Sou {nome}, profissional nível {nivel}. Tenho experiência sólida em {', '.join(skills)}. Busco oportunidades desafiadoras.")
                
                # Skills
                for s in skills:
                    Skill.objects.create(candidato=c, nome=s, tipo='hard')
                
                # Experiência Genérica
                Experiencia.objects.create(
                    candidato=c, cargo=headline, empresa='Empresa Anterior S.A.',
                    data_inicio=datetime.date(2022, 1, 1), data_fim=datetime.date(2024, 1, 1),
                    descricao=f'Atuei como {headline} utilizando {skills[0]} e {skills[1]}.'
                )

        self.stdout.write(self.style.SUCCESS('🚀 SEED ROBUSTO CONCLUÍDO! 15 Candidatos, 3 Empresas criados.'))