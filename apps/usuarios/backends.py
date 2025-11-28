from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import Candidato, Recrutador, Empresa
import re

UserModel = get_user_model()

class EmailOrCPFBackend(ModelBackend):
    """
    Autentica um usuário usando seu email ou CPF, conforme UC03.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_identifier = username
        user = None 

        try:
            # 1. Tentar encontrar o usuário pelo E-mail
            user = UserModel.objects.get(email__iexact=login_identifier)

        except UserModel.DoesNotExist:
            try:
                # 2. Se não achou por email, tentar encontrar pelo CPF
                cpf_digits = re.sub(r'[^0-9]', '', login_identifier)
                if len(cpf_digits) == 11:
                    candidato = Candidato.objects.get(cpf=cpf_digits)
                    user = candidato.usuario

            except Candidato.DoesNotExist:
                try:
                    # 3. Se não achou por CPF, tentar encontrar pelo CNPJ
                    cnpj_digits = re.sub(r'[^0-9]', '', login_identifier)
                    if len(cnpj_digits) == 14:
                        empresa = Empresa.objects.get(cnpj=cnpj_digits)
                        recrutador = Recrutador.objects.filter(empresa=empresa).first()
                        if recrutador:
                            user = recrutador.usuario

                except (Empresa.DoesNotExist, Recrutador.DoesNotExist):
                    user = None

        # 4. Checa a senha e se o usuário está ativo
        if user:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user 

        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None