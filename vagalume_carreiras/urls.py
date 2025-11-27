# Arquivo: vagalume_carreiras/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),

    # 2. Adicione esta linha:
    # Ela diz ao Django: "Qualquer URL que comece com 'contas/'...
    # ...deve ser gerenciada pelo nosso arquivo 'apps.usuarios.urls'".
    path('contas/', include('apps.usuarios.urls')),

    # (Mais tarde, faremos o mesmo para o app de vagas)
    # path('', include('apps.vagas.urls')),
    path('', include('apps.vagas.urls')),

    path('sobre-nos/', TemplateView.as_view(template_name='sobre_nos.html'), name='sobre_nos')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)