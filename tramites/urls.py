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
        'asignados-old/',
        RedirectView.as_view(
            url=reverse_lazy('admin:tramites_tramite_changelist', query={'asignado': 'True'}),
            permanent=True,
        ),
        name='asignados',
    ),
    path(
        'finalizados-old/',
        RedirectView.as_view(
            url=reverse_lazy('admin:tramites_tramite_changelist', query={'finalizado': 'True'}),
            permanent=True,
        ),
        name='finalizados',
    ),
    path(
        'cancelados-old/',
        RedirectView.as_view(
            url=reverse_lazy('admin:tramites_tramite_changelist', query={'cancelado': 'True'}),
            permanent=True,
        ),
        name='cancelados',
    ),
    path(
        'tramite/<int:pk>/download/<str:filename>/',
        views.download_requisito_pdf,
        name='download-requisito-pdf',
    ),
]
