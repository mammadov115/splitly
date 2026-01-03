from django import forms
from .models import Expense
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


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


class ExtendedUserCreationForm(UserCreationForm):
    fullname = forms.CharField(max_length=100, required=True, label="Tam Ad")

    class Meta(UserCreationForm.Meta):
        model = User
        # 'fullname' sahəsini bura əlavə etmirik, çünki bazada yoxdur.
        # Sadəcə istifadəçidən məlumatı almaq üçün yuxarıda CharField kimi təyin etdik.
        fields = UserCreationForm.Meta.fields

    def save(self, commit=True):
        user = super().save(commit=False)
        fullname = self.cleaned_data.get("fullname")

        if fullname:
            # Adı və soyadı ayırırıq
            parts = fullname.split(' ', 1) # Maksimum 1 dəfə bölür (ad və qalan hissə)
            if len(parts) > 1:
                user.first_name = parts[0]
                user.last_name = parts[1]
            else:
                user.first_name = parts[0]
                user.last_name = "" # Soyad yazılmayıbsa boş qalsın

        if commit:
            user.save()
        return user