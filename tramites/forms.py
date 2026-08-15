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
            attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Describe el motivo de esta acción...',
            }
        ),
        help_text='Observación requerida para esta acción',
    )


# Estatus de cancelación disponibles para el dropdown.
# Se define como módulo-level constant para reutilización en form y template.
ESTATUS_CANCELACION_CHOICES = (
    (TramiteEstatus.Estatus.POR_RECOGER, 'Por Recoger'),
    (TramiteEstatus.Estatus.RECHAZADO, 'Rechazado'),
    (TramiteEstatus.Estatus.CANCELADO, 'Cancelado'),
)


class CancelarTramiteForm(forms.Form):
    """Formulario intermedio para cancelar un trámite.

    Requiere que el usuario seleccione un estatus de cancelación y proporcione
    una observación obligatoria explicando el motivo de la cancelación.

    Los estatus ofrecidos se limitan a los destinos de cierre válidos para el
    estatus actual del trámite (``tramites.workflow.closure_targets()``).
    """

    estatus_cierre = forms.ChoiceField(
        label='Estatus de cancelación',
        choices=ESTATUS_CANCELACION_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Selecciona el estatus con el que se cancelará el trámite',
    )
    observacion = forms.CharField(
        label='Motivo de cancelación',
        required=True,
        widget=forms.Textarea(
            attrs={
                'rows': 4,
                'placeholder': 'Explica el motivo por el que se cancela este trámite...',
                'class': 'form-control',
            }
        ),
        help_text='La observación es obligatoria para cancelar un trámite',
    )

    def __init__(self, *args, estatus_choices=None, **kwargs):
        """Init con choices dinámicos según el estatus origen del trámite.

        Args:
            estatus_choices: Iterable ``(value, label)`` con los destinos de
                cierre válidos. Si es ``None`` usa el default completo
                (301/302/304) — la validación de transición en el modelo sigue
                siendo la última línea de defensa.
        """
        super().__init__(*args, **kwargs)
        if estatus_choices is not None:
            self.fields['estatus_cierre'].choices = list(estatus_choices)
