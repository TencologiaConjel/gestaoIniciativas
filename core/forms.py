from django import forms
from .models import Ideia

class IdeiaForm(forms.ModelForm):
    class Meta:
        model = Ideia
        fields = [
            'titulo', 'descricao', 'tipo_beneficio', 'alinhamento_okr',
            'esforco_estimado', 'publicos_impactados', 'riscos_identificados',
            'risco_outro_descricao', 'metrica_sucesso', 'equipes_necessarias', 'referencias'
        ]
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
            'metrica_sucesso': forms.Textarea(attrs={'rows': 2}),
            'referencias': forms.Textarea(attrs={'rows': 2}),
            'publicos_impactados': forms.CheckboxSelectMultiple(),
            'equipes_necessarias': forms.CheckboxSelectMultiple(),
            'riscos_identificados': forms.CheckboxSelectMultiple(),
        }
