from django import forms
from Meeting.models import Vote


class VoteForm(forms.Form):
    name = forms.CharField(label='Name', max_length=150)
    description = forms.CharField(label="Description", widget=forms.Textarea, required=False)
    method = forms.ChoiceField(label="Method", choices=Vote.methods)
