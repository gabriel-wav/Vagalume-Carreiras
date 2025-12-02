from django.db import models
from apps.usuarios.models import Candidato, Empresa, Recrutador

class Vaga(models.Model):
    # Conecta a Vaga à Empresa que a publicou
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    # Conecta a Vaga ao Recrutador que a criou
    recrutador = models.ForeignKey(Recrutador, on_delete=models.CASCADE)

    # --- NOVO CAMPO: ÁREA DE ATUAÇÃO ---
    AREAS_CHOICES = [
        ('tecnologia', 'Tecnologia e Programação'),
        ('design', 'Design e UX/UI'),
        ('marketing', 'Marketing e Vendas'),
        ('financeiro', 'Financeiro e Contabilidade'),
        ('rh', 'Recursos Humanos'),
        ('engenharia', 'Engenharia'),
        ('saude', 'Saúde'),
        ('educacao', 'Educação'),
        ('operacional', 'Operacional e Logística'),
        ('outros', 'Outros'),
    ]
    
    titulo = models.CharField(max_length=100)
    
    area_atuacao = models.CharField(
        max_length=50, 
        choices=AREAS_CHOICES, 
        default='outros',
        verbose_name="Área de Atuação"
    )

    descricao = models.TextField()
    requisitos = models.TextField()
    tipo_contrato = models.CharField(max_length=50)
    localidade = models.CharField(max_length=100)
    beneficios = models.TextField(blank=True, null=True)
    faixa_salarial = models.CharField(max_length=50, blank=True, null=True)
    status = models.BooleanField(default=True) # True = Aberta, False = Fechada
    data_publicacao = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.titulo

class Candidatura(models.Model):
    # Esta é a tabela que LIGA o Candidato e a Vaga
    candidato = models.ForeignKey(Candidato, on_delete=models.CASCADE)
    vaga = models.ForeignKey(Vaga, on_delete=models.CASCADE)

    data_candidatura = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=50, default='Enviada') 
    
    class Meta:
        # Garante que um candidato não possa se aplicar 2x na mesma vaga
        unique_together = ('candidato', 'vaga')

class Plano(models.Model):
    NOME_PLANOS = [
        ('basico', 'Básico (Grátis)'),
        ('intermediario', 'Intermediário'),
        ('premium', 'Premium'),
    ]

    nome_chave = models.CharField(max_length=20, choices=NOME_PLANOS, unique=True)
    nome_exibicao = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    limite_vagas = models.IntegerField(default=1)
    descricao_curta = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.nome_exibicao
        
    class Meta:
        verbose_name = "Plano de Assinatura"
        verbose_name_plural = "Planos de Assinatura"