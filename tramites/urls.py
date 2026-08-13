from django.urls import path, reverse_lazy
from django.views.generic import RedirectView

from . import views

app_name = 'tramites'

urlpatterns = [
    path(
        'sin_asignar/',
        RedirectView.as_view(
            url=reverse_lazy('admin:tramites_tramite_changelist', query={'asignado': 'False'}),
            permanent=True,
        ),
        name='sin-asignar',
    ),
    path(
        'tramite/<int:pk>/cancelar/',
        views.cancelar_tramite_view,
        name='cancelar-tramite',
    ),
    path(
        'tramite/<int:pk>/download/<str:filename>/',
        views.download_pdf,
        name='download-pdf',
    ),
]
