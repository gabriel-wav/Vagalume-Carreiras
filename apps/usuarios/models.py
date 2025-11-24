from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.conf import settings

class Usuario(AbstractUser):
    
    TIPO_USUARIO_CHOICES = (
        ('candidato', 'Candidato'),
        ('recrutador', 'Recrutador'),
    )
    
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TIPO_USUARIO_CHOICES,
        default='candidato'
    )
    telefone = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return self.email

# -------------------------------------------------------------------
# "Empresa" (não é um usuario)
# A Empresa não loga. O Recrutador loga EM NOME dela.
# -------------------------------------------------------------------
class Empresa(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    cnpj = models.CharField(max_length=14, unique=True)
    setor = models.CharField(max_length=100)

    def __str__(self):
        return self.nome
    
# -------------------------------------------------------------------
# Estes models se conectam ao model "Usuario"
# para guardar os dados específicos de cada um.
# -------------------------------------------------------------------

class Candidato(models.Model):
    # Conecta o Perfil Candidato ao sistema de Login
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, # Aponta para o nosso model "Usuario"
        on_delete=models.CASCADE,   # Se o login for apagado, o perfil também é
        primary_key=True          # O ID do Candidato será o mesmo ID do Usuario
    )
    
    # CAMPOS ESPECÍFICOS (Removemos nome, email, senha, etc., pois estão no Usuario)
    cpf = models.CharField(max_length=11, unique=True)
    headline = models.CharField(max_length=255, blank=True, null=True)
    curriculo_pdf = models.FileField(upload_to='curriculos_pdf/', blank=True, null=True)
    
    GENERO_CHOICES = (
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('P', 'Prefiro não informar'),
    )
    genero = models.CharField(
        max_length=1, 
        choices=GENERO_CHOICES, 
        blank=True, 
        null=True
    )
    bairro = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.usuario.email # Puxa o email do sistema de login

class Recrutador(models.Model):
    # Conecta o Perfil Recrutador ao sistema de Login
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True
    )
    
    # Conecta o Recrutador à Empresa que ele representa
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.usuario.email} ({self.empresa.nome})"

# NOTA: O 'Administrador' foi removido. O próprio 'Usuario' 
# com 'is_staff=True' e 'is_superuser=True' já é o administrador.

# Todos estes se conectam ao 'Candidato' com uma chave estrangeira

class Resumo_Profissional(models.Model):
    candidato = models.OneToOneField(Candidato, on_delete=models.CASCADE) # Um candidato só tem um resumo
    texto = models.TextField(max_length=500)

class Idiomas(models.Model):
    candidato = models.ForeignKey(Candidato, related_name='idiomas', on_delete=models.CASCADE)
    idioma = models.CharField(max_length=50)
    nivel = models.CharField(max_length=50)

class Redes_Sociais(models.Model):
    candidato = models.ForeignKey(Candidato, related_name='redes_sociais', on_delete=models.CASCADE)
    tipo_rede = models.CharField(max_length=50) # Ex: 'LinkedIn', 'GitHub'
    link = models.URLField(max_length=200)

class Skill(models.Model):
    candidato = models.ForeignKey(Candidato, related_name='skills', on_delete=models.CASCADE)
    TIPO_SKILL_CHOICES = (
        ('hard', 'Hard Skill'),
        ('soft', 'Soft Skill'),
    )
    nome = models.CharField(max_length=100) # Nome da skill (ex: 'Python', 'Comunicação')
    tipo = models.CharField(max_length=10, choices=TIPO_SKILL_CHOICES)

class Experiencia(models.Model):
    candidato = models.ForeignKey(Candidato, related_name='experiencias', on_delete=models.CASCADE)
    cargo = models.CharField(max_length=100)
    empresa = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    trabalha_atualmente = models.BooleanField(default=False)
    descricao = models.TextField(blank=True, null=True)

class Formacao_Academica(models.Model):
    candidato = models.ForeignKey(Candidato, related_name='formacoes', on_delete=models.CASCADE)
    nome_instituicao = models.CharField(max_length=100)
    nome_formacao = models.CharField(max_length=100)
    nivel = models.CharField(max_length=50)
    estado = models.CharField(max_length=50)
    cidade = models.CharField(max_length=50)
    formacao_exterior = models.BooleanField(default=False)
    data_inicio = models.DateField()
    data_fim = models.DateField(blank=True, null=True)
    cursando_atualmente = models.BooleanField(default=False)