# Arquivo: vagalume_carreiras/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView # <--- Importante!

urlpatterns = [
    path('admin/', admin.site.urls),
    path('contas/', include('apps.usuarios.urls')),
    path('', include('apps.vagas.urls')),

    # Rota direta para o template estático
    path('sobre-nos/', TemplateView.as_view(template_name='sobre_nos.html'), name='sobre_nos'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)