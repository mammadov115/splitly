from django import forms
from .models import Expense
from django.contrib.auth.models import User

class ExpenseForm(forms.ModelForm):
    # Field to select users to split the expense with
    split_with = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    class Meta:
        model = Expense
        fields = ['title', 'amount', 'split_with']