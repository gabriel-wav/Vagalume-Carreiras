from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

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
    
    # Email é o campo principal de login e deve ser único
    email = models.EmailField('email address', unique=True, blank=False)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    
    def __str__(self):
        return self.email

# -------------------------------------------------------------------
# MODELO EMPRESA
# -------------------------------------------------------------------
class Empresa(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=15, blank=True, null=True)
    cnpj = models.CharField(max_length=14, unique=True)
    setor = models.CharField(max_length=100)

    # --- NOVOS CAMPOS DE PLANO ---
    # Usa string 'vagas.Plano' para evitar erro de importação circular
    plano_fk = models.ForeignKey(
        'vagas.Plano', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='Plano (Chave Estrangeira)'
    )

    OPCOES_PLANO = [
        ('basico', 'Plano Básico'),
        ('intermediario', 'Plano Intermediário'),
        ('premium', 'Plano Premium'),
    ]
    
    plano_assinado = models.CharField(
        max_length=20,
        choices=OPCOES_PLANO,
        default='basico',
        verbose_name='Plano Assinado (Regra de Negócio)'
    )
    # -----------------------------

    def __str__(self):
        return self.nome
    
# -------------------------------------------------------------------
# Outros Modelos
# -------------------------------------------------------------------

class Candidato(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True
    )
    cpf = models.CharField(max_length=11, unique=True)
    headline = models.CharField(max_length=255, blank=True, null=True)
    curriculo_pdf = models.FileField(upload_to='curriculos_pdf/', blank=True, null=True)
    
    GENERO_CHOICES = (
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
        ('P', 'Prefiro não informar'),
    )
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, blank=True, null=True)
    bairro = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.usuario.email

class Recrutador(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True
    )
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.usuario.email} ({self.empresa.nome})"

class Resumo_Profissional(models.Model):
    candidato = models.OneToOneField(Candidato, on_delete=models.CASCADE)
    texto = models.TextField(max_length=500)

class Idiomas(models.Model):
    candidato = models.ForeignKey(Candidato, related_name='idiomas', on_delete=models.CASCADE)
    idioma = models.CharField(max_length=50)
    nivel = models.CharField(max_length=50)

class Redes_Sociais(models.Model):
    candidato = models.ForeignKey(Candidato, related_name='redes_sociais', on_delete=models.CASCADE)
    tipo_rede = models.CharField(max_length=50)
    link = models.URLField(max_length=200)

class Skill(models.Model):
    candidato = models.ForeignKey(Candidato, related_name='skills', on_delete=models.CASCADE)
    TIPO_SKILL_CHOICES = (('hard', 'Hard Skill'), ('soft', 'Soft Skill'))
    nome = models.CharField(max_length=100)
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

class AvaliacaoEmpresa(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='avaliacoes')
    candidato = models.ForeignKey(Candidato, on_delete=models.CASCADE)
    nota = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentario = models.TextField(blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('empresa', 'candidato')

    def __str__(self):
        return f"{self.empresa.nome} - {self.nota} estrelas"

class RecuperacaoSenha(models.Model):
    METODO_CHOICES = [('email', 'E-mail'), ('sms', 'SMS')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    metodo = models.CharField(max_length=5, choices=METODO_CHOICES)
    criado_em = models.DateTimeField(auto_now_add=True)
    expira_em = models.DateTimeField()
    usado = models.BooleanField(default=False)

    class Meta:
        db_table = 'recuperacao_senha'
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.user.username} - {self.codigo} ({self.metodo})"