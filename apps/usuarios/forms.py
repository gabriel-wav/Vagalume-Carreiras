from django import forms
from .models import Usuario, Candidato, Experiencia, Formacao_Academica, Skill, Empresa
import re

class CandidatoCadastroForm(forms.Form):
    """
    Formulário para o fluxo UC01: Cadastrar Novo Candidato.
    Coleta dados para os models Usuario e Candidato.
    """
    
    first_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Nome'}))
    last_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Sobrenome'}))
    email = forms.EmailField(label='', widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    telefone = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Telefone'}))
    cpf = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'CPF'}))
    password = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))
    password_confirm = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar Senha'}))

def clean_cpf(self):
        # Validação do CPF 
        cpf = self.cleaned_data.get('cpf')
        cpf_digits = re.sub(r'[^0-9]', '', cpf) # Remove pontos e traços
        
        if len(cpf_digits) != 11:
            raise forms.ValidationError("CPF deve conter 11 dígitos.")
        
        # Validação de unicidade
        if Candidato.objects.filter(cpf=cpf_digits).exists():
            raise forms.ValidationError("Este CPF já está cadastrado. Tente fazer login.")
        
        return cpf_digits # Retorna o CPF limpo

def clean_email(self):
        # Validação de unicidade do Email
        email = self.cleaned_data.get('email').lower()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email já está cadastrado. Tente fazer login.") 
        return email

def clean(self):
        # Validação para checar se as senhas coincidem
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("As senhas não coincidem.")
        
        return cleaned_data

def clean_telefone(self):
    # Validação de unicidade do Telefone
    telefone = self.cleaned_data.get('telefone')
    # (Opcional: limpar o telefone de máscaras, similar ao CPF)
    # telefone_digits = re.sub(r'[^0-9]', '', telefone) 

    if Usuario.objects.filter(telefone=telefone).exists():
        raise forms.ValidationError("Este telefone já está cadastrado.")
    return telefone

class ExperienciaForm(forms.ModelForm):
    """
    Formulário para a Etapa "Experiências" do Onboarding.
    """
    class Meta:
        model = Experiencia
        # O 'candidato' será adicionado na view, então não colocamos aqui
        fields = [
            'cargo', 'empresa', 'data_inicio', 'data_fim', 
            'trabalha_atualmente', 'descricao'
        ]
        # Opcional: Deixar os campos de data mais bonitos
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

class FormacaoForm(forms.ModelForm):
    """
    Formulário para a Etapa "Formação Acadêmica" do Onboarding.
    """
    class Meta:
        model = Formacao_Academica
        fields = [
            'nome_instituicao', 'nome_formacao', 'nivel', 
            'data_inicio', 'data_fim', 'cursando_atualmente'
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
        }

class SkillForm(forms.ModelForm):
    """
    Formulário para a Etapa "Skills" do Onboarding.
    """
    class Meta:
        model = Skill
        fields = ['nome', 'tipo'] # O ModelForm cria o dropdown 'tipo' sozinho!

class CurriculoForm(forms.ModelForm):
    """
    Formulário para a Etapa Final "Currículo PDF" do Onboarding.
    """
    class Meta:
        model = Candidato
        fields = ['curriculo_pdf'] # Pega só aquele campo que criamos

class RecrutadorCadastroForm(forms.Form):
    """
    Formulário para o fluxo de cadastro de Recrutador (Empresa).
    Coleta dados para os models Usuario, Empresa e Recrutador.
    """
    
    # --- Dados do Usuário (Recrutador) ---
    first_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Seu Nome'}))
    last_name = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Seu Sobrenome'}))
    email = forms.EmailField(label='', widget=forms.EmailInput(attrs={'placeholder': 'Email Corporativo'}))
    telefone = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Telefone Comercial'}))
    password = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))
    password_confirm = forms.CharField(label='', widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar Senha'}))
    
    # --- Dados da Empresa ---
    nome_empresa = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Nome da Empresa'}))
    cnpj = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'CNPJ (apenas números)'}))
    setor = forms.CharField(label='', widget=forms.TextInput(attrs={'placeholder': 'Setor (Ex: Tecnologia)'}))

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este email corporativo já está cadastrado.")
        return email

    def clean_cnpj(self):
        cnpj = self.cleaned_data.get('cnpj')
        cnpj_digits = re.sub(r'[^0-9]', '', cnpj)
        if len(cnpj_digits) != 14:
            raise forms.ValidationError("CNPJ deve conter 14 dígitos.")
        if Empresa.objects.filter(cnpj=cnpj_digits).exists():
            raise forms.ValidationError("Este CNPJ já está cadastrado em nossa plataforma.")
        return cnpj_digits

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "As senhas não coincidem.")
        
        return cleaned_data

# apps/usuarios/forms.py

class PerfilUsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'telefone']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Nome'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Sobrenome'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(XX) XXXXX-XXXX'}),
        }

class PerfilCandidatoForm(forms.ModelForm):
    class Meta:
        model = Candidato
        fields = ['headline', 'genero', 'bairro']
        widgets = {
            'headline': forms.TextInput(attrs={'placeholder': 'Ex: Desenvolvedor Full Stack'}),
            'bairro': forms.TextInput(attrs={'placeholder': 'Seu Bairro'}),
        }
        
class NovaSenhaForm(forms.Form):
    """
    Formulário para definir a nova senha.
    """
    new_password = forms.CharField(label='Nova Senha', widget=forms.PasswordInput(attrs={'placeholder': 'Nova Senha'}))
    confirm_password = forms.CharField(label='Confirmar Senha', widget=forms.PasswordInput(attrs={'placeholder': 'Confirmar Senha'}))

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            raise forms.ValidationError("As senhas não coincidem.")
        
        # Nota: A validação de complexidade de senha (UserAttributeSimilarityValidator, etc.)
        # deve ser aplicada na view (nova_senha_view).
        
        return cleaned_data