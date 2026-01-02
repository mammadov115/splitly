from django.views.generic import ListView
from django.shortcuts import redirect
from .models import Expense, ExpenseSplit
from .forms import ExpenseForm
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin

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
    form_class = UserCreationForm
    template_name = 'login.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        # Hesab yaradılan kimi avtomatik login etdiririk
        valid = super().form_valid(form)
        login(self.request, self.object)
        return valid

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('login')