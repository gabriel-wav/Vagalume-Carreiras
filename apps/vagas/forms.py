from django import forms
from .models import Vaga

class VagaForm(forms.ModelForm):
    """
    Formulário para o Recrutador criar ou editar uma Vaga.
    """
    class Meta:
        model = Vaga
        # Define os campos que o recrutador irá preencher
        fields = [
            'titulo', 
            'area_atuacao', # <--- NOVO CAMPO AQUI
            'descricao', 
            'requisitos', 
            'tipo_contrato', 
            'localidade', 
            'beneficios', 
            'faixa_salarial', 
            'status'
        ]
        
        # Widgets para estilização
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Descreva as atividades...'}),
            'requisitos': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Ex: Python, SQL, Inglês...'}),
            'beneficios': forms.Textarea(attrs={'rows': 3, 'placeholder': 'VT, VR, Plano de Saúde...'}),
            'area_atuacao': forms.Select(attrs={'class': 'form-control', 'style': 'background-color:#0D1117; color:#fff; border:1px solid #30363d;'}),
            'status': forms.RadioSelect(choices=[(True, 'Vaga Aberta'), (False, 'Vaga Fechada (Arquivada)')],
            attrs={'class': 'radio-custom'}),
        }
        
        labels = {
            'titulo': 'Título da Vaga',
            'area_atuacao': 'Área de Atuação',
            'localidade': 'Cidade/Estado ou Remoto',
        }

    def __init__(self, *args, **kwargs):
        self.empresa = kwargs.pop('empresa', None)
        super().__init__(*args, **kwargs)
        
        # Adiciona classes de CSS padrão para os inputs
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def clean_titulo(self):
        """
        Impede que a mesma empresa cadastre duas vagas com o mesmo título exato.
        """
        titulo = self.cleaned_data.get('titulo')
        
        if not self.empresa:
            # Se for edição ou algo interno
            return titulo

        query = Vaga.objects.filter(
            empresa=self.empresa, 
            titulo__iexact=titulo
        )
        
        if self.instance and self.instance.pk:
            query = query.exclude(pk=self.instance.pk)
        
        if query.exists():
            raise forms.ValidationError("Sua empresa já possui uma vaga cadastrada com este título.")
            
        return titulo

    def save(self, commit=True, recrutador=None):
        vaga = super().save(commit=False)
        
        if recrutador:
            vaga.recrutador = recrutador
            vaga.empresa = recrutador.empresa
        elif self.empresa:
             vaga.empresa = self.empresa
            
        if commit:
            vaga.save()
            
        return vaga