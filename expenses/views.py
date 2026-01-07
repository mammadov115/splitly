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
from django.http import HttpResponse
from django.db.models import F, FilteredRelation, Q

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

        user = self.request.user
        base_queryset = Expense.objects.prefetch_related('splits__user').select_related('paid_by').all().order_by('-date')
        context['my_paid_expenses'] = base_queryset.filter(paid_by=user)

        # Digərlərinin ödədiyi xərclər
        others_paid = Expense.objects.filter(
            split_with=user
        ).exclude(
            paid_by=user
        ).prefetch_related(
            'splits'
        ).annotate(
            # Cari userin bu xərcdəki split məlumatını tapırıq
            user_share=F('splits__amount_owed'),
            user_is_settled=F('splits__is_settled')
        ).filter(
            splits__user=user # Yalnız cari userin splitini annotasiya et
        ).order_by('-date')
        context['others_paid_expenses'] = others_paid

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
def add_expense_ajax(request):
    print("AJAX request body:", request.body)
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

        # 3. Yeni sttausu göndərmək
        return HttpResponse(status=200)

    except Exception as e:
        print("Error:", e)
        return HttpResponse(status=400)