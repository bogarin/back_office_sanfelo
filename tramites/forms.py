"""Formularios para gestión de trámites."""

from django import forms


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
