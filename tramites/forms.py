"""Formularios para gestión de trámites."""

from django import forms

from tramites.models.catalogos import TramiteEstatus


class TramiteDetailForm(forms.Form):
    """
    Formulario para vista de detalle de trámite.

    NOTA: No es un ModelForm (modelo es readonly vista).
    Solo contiene campo para observación de acciones.
    """

    # Observación obligatoria para todas las acciones
    observacion = forms.CharField(
        label='Observación',
        required=True,
        widget=forms.Textarea(
            attrs={'rows': 3, 'placeholder': 'Describe el motivo de esta acción...'}
        ),
        help_text='Observación requerida para esta acción',
    )


# Estatus de cierre disponibles para el dropdown.
# Se define como módulo-level constant para reutilización en form y template.
ESTATUS_CIERRE_CHOICES = (
    (TramiteEstatus.Estatus.POR_RECOGER, 'Por Recoger'),
    (TramiteEstatus.Estatus.RECHAZADO, 'Rechazado'),
    (TramiteEstatus.Estatus.CANCELADO, 'Cancelado'),
)


class CerrarTramiteForm(forms.Form):
    """Formulario intermedio para cerrar un trámite.

    Requiere que el analista seleccione un estatus de cierre y proporcione
    una observación obligatoria explicando el motivo del cierre.
    """

    estatus_cierre = forms.ChoiceField(
        label='Estatus de cierre',
        choices=ESTATUS_CIERRE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Selecciona el estatus con el que se cerrará el trámite',
    )
    observacion = forms.CharField(
        label='Motivo de cierre',
        required=True,
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'placeholder': 'Explica el motivo por el que se cierra este trámite...',
                'class': 'form-control',
            }
        ),
        help_text='La observación es obligatoria para cerrar un trámite',
    )
