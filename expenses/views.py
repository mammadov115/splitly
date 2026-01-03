from django.views.generic import ListView
from django.shortcuts import redirect
from .models import Expense, ExpenseSplit
from .forms import ExpenseForm, ExtendedUserCreationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json
from decimal import Decimal

class HomeView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'home.html'
    context_object_name = 'expenses'
    ordering = ['-date']
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ExpenseForm()
        # Adding splits to context for display purposes
        context['splits'] = ExpenseSplit.objects.select_related('expense', 'user').all()
        context['all_users'] = User.objects.exclude(id=self.request.user.id)
        return context

    def post(self, request, *args, **kwargs):
        form = ExpenseForm(request.POST)
        if form.is_valid():
            # Xərci yadda saxlayırıq amma hələ commit etmirik ki, paid_by əlavə edək
            expense = form.save(commit=False)
            expense.paid_by = request.user
            expense.save()
            
            # Formdan seçilən adamları götürürük və modeldəki metodumuzu çağırırıq
            users_to_split = form.cleaned_data['split_with']
            expense.split_expense(users_to_split)
            
            return redirect('home')
        return self.get(request, *args, **kwargs)
    

class UserLoginView(LoginView):
    template_name = 'login.html' # Login və Register üçün eyni faylı istifadə edəcəyik
    redirect_authenticated_user = True # Giriş edibsə birbaşa home-a atır
    
    def get_success_url(self):
        return reverse_lazy('home')

class UserRegisterView(CreateView):
    form_class = ExtendedUserCreationForm
    template_name = 'login.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        print("Yeni istifadəçi qeydiyyatdan keçdi:", form.cleaned_data)
        # Hesab yaradılan kimi avtomatik login etdiririk
        valid = super().form_valid(form)
        login(self.request, self.object)
        return valid

    # Əgər formda xəta olsa bu metod işə düşəcək
    def form_invalid(self, form):
        print("Form xətaları:", form.errors) # Xətaları terminalda görəcəksiniz
        return super().form_invalid(form)

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')


@login_required
@require_POST
def add_expense_ajax(request):
    print("AJAX vasitəsilə yeni xərc əlavə edilir")
    try:
        data = json.loads(request.body)
        title = data.get('title')
        amount = Decimal(str(data.get('amount')))
        user_ids = data.get('split_with', []) # Seçilmiş user ID-ləri siyahısı

        if not title or amount <= 0:
            return JsonResponse({'success': False, 'error': 'Məlumatlar tam deyil'}, status=400)

        # 1. Xərci yaradan (Ödəyən hazırkı userdir)
        expense = Expense.objects.create(
            title=title,
            amount=amount,
            paid_by=request.user
        )

        # 2. Xərci bölmək (Əgər heç kim seçilməyibsə, yalnız özünə yazır)
        if not user_ids:
            user_ids = [request.user.id]
        
        users_to_split = User.objects.filter(id__in=user_ids)
        expense.split_expense(users_to_split)

        # 3. Alpine.js-ə yeni datanı göndərmək
        return JsonResponse({
            'success': True,
            'expense': {
                'id': expense.id,
                'title': expense.title,
                'amount': float(expense.amount),
                'date': expense.date.strftime('%d.%m.%Y'),
                'paid_by': expense.paid_by.username
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)