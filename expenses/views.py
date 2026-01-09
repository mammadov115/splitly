from django.views.generic import ListView, CreateView
from django.shortcuts import redirect
from .models import Expense, ExpenseSplit
from .forms import ExpenseForm, ExtendedUserCreationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import OuterRef, Subquery
import json
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404


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
        context['all_users'] = User.objects.exclude(id=self.request.user.id).exclude(is_superuser=True)
        
        user = self.request.user
        # 1. Cari user-in həmin xərcdəki split-ini tapmaq üçün alt-sorğu (Subquery)
        user_shares = ExpenseSplit.objects.filter(
            expense=OuterRef('pk'), 
            user=user
        )

        # 2. Xərcləri gətirərkən məlumatları üzərinə yazırıq
        expenses = Expense.objects.select_related('paid_by').prefetch_related('splits__user').annotate(
            my_split_id=Subquery(user_shares.values('pk')[:1]),
            my_share=Subquery(user_shares.values('amount_owed')[:1]),
            is_settled=Subquery(user_shares.values('is_settled')[:1]),
            waiting_for_settlement=Subquery(user_shares.values('waiting_for_settlement')[:1])
        ).order_by('-date')
        # expenses = Expense.objects.prefetch_related('splits__user').select_related('paid_by').all().order_by('-date')
        
        
        for e in expenses:
            if e.paid_by == user:
                e.card_template = "partials/card_paid_by_me.html"
            else:
                e.card_template = "partials/card_paid_by_others.html"
        context['expenses'] = expenses
        
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


@require_POST
@csrf_exempt
def settle_request_view(request, split_id):
    # Yalnız həmin splitin sahibi bu istəyi göndərə bilər
    split = get_object_or_404(ExpenseSplit, id=split_id, user=request.user)
    
    split.waiting_for_settlement = True
    split.save()
    
    return JsonResponse({'status': 'success', 'message': 'Təsdiq gözlənilir'})