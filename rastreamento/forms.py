from django import forms
from .models import Dispositivo, Pessoa


class PessoaForm(forms.ModelForm):
    class Meta:
        model = Pessoa
        fields = ['nome', 'descricao']
        widgets = {'descricao': forms.Textarea(attrs={'rows': 2})}


class DispositivoForm(forms.ModelForm):
    class Meta:
        model = Dispositivo
        fields = ['pessoa', 'nome']

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pessoa'].queryset = Pessoa.objects.filter(responsavel=user)
