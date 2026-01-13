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
from django.db.models import OuterRef, Subquery, Sum
import json
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from expenses.utils import send_live_notification




class HomeView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'home.html'
    context_object_name = 'expenses'
    ordering = ['-date']
    login_url = 'login'
    paginate_by = 5  # Hər səhifədə neçə xərc görünüsn

    def get_queryset(self):
            user = self.request.user
            # 1. Cari user-in həmin xərcdəki split-ini tapmaq üçün Subquery
            user_shares = ExpenseSplit.objects.filter(
                expense=OuterRef('pk'), 
                user=user
            )

            # 2. Əsas sorğu (Bunu get_queryset-ə köçürdük ki, ListView pagination-ı idarə edə bilsin)
            queryset = Expense.objects.select_related('paid_by').prefetch_related('splits__user').annotate(
                my_split_id=Subquery(user_shares.values('pk')[:1]),
                my_share=Subquery(user_shares.values('amount_owed')[:1]),
                is_settled=Subquery(user_shares.values('is_settled')[:1]),
                waiting_for_settlement=Subquery(user_shares.values('waiting_for_settlement')[:1])
            ).order_by('-date')
            
            # Template seçimi üçün loop
            for e in queryset:
                if e.paid_by == user:
                    e.card_template = "partials/card_paid_by_me.html"
                else:
                    e.card_template = "partials/card_paid_by_others.html"
            
            return queryset    

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context['form'] = ExpenseForm()
        # Adding splits to context for display purposes
        context['splits'] = ExpenseSplit.objects.select_related('expense', 'user').all()
        context['all_users'] = User.objects.exclude(id=self.request.user.id).exclude(is_superuser=True)
        context['has_new_notifications'] = ExpenseSplit.objects.filter(
            expense__paid_by=user, 
            waiting_for_settlement=True,
            is_viewed_by_creator=False
        ).exists()

        
        # # 1. Cari user-in həmin xərcdəki split-ini tapmaq üçün alt-sorğu (Subquery)
        # user_shares = ExpenseSplit.objects.filter(
        #     expense=OuterRef('pk'), 
        #     user=user
        # )

        # # 2. Xərcləri gətirərkən məlumatları üzərinə yazırıq
        # expenses = Expense.objects.select_related('paid_by').prefetch_related('splits__user').annotate(
        #     my_split_id=Subquery(user_shares.values('pk')[:1]),
        #     my_share=Subquery(user_shares.values('amount_owed')[:1]),
        #     is_settled=Subquery(user_shares.values('is_settled')[:1]),
        #     waiting_for_settlement=Subquery(user_shares.values('waiting_for_settlement')[:1])
        # ).order_by('-date')
        # # expenses = Expense.objects.prefetch_related('splits__user').select_related('paid_by').all().order_by('-date')
        
        
        # for e in expenses:
        #     if e.paid_by == user:
        #         e.card_template = "partials/card_paid_by_me.html"
        #     else:
        #         e.card_template = "partials/card_paid_by_others.html"
        # context['expenses'] = expenses
        
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
        

        # --- BİLDİRİŞ GÖNDƏRMƏ HİSSƏSİ ---
        notification_title = "Yeni Xərc!"
        notification_body = f"{request.user.username} '{title}' aldı. Sənə bu xərcdən {expense.my_split} düşür."

        for user_to_notify in users_to_split:
            # Özümüzə bildiriş göndərmirik
            if user_to_notify != request.user:
                # 1. Firebase Live Push Notification
                try:
                    send_live_notification(
                        user=user_to_notify,
                        title=notification_title,
                        body=notification_body
                    )
                except Exception as fcm_error:
                    print(f"FCM Error for {user_to_notify.username}: {fcm_error}")


        
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


class NotificationListView(LoginRequiredMixin, ListView):
    model = ExpenseSplit
    template_name = 'notifications.html'
    context_object_name = 'incoming_approvals'

    def get_queryset(self):
        # Yalnız cari istifadəçinin yaratdığı xərclər üzrə təsdiq gözləyən splitlər
        qs = ExpenseSplit.objects.filter(
            expense__paid_by=self.request.user,
            waiting_for_settlement=True
        ).exclude(user=self.request.user).select_related('expense', 'user').order_by('-id')

        qs.filter(is_viewed_by_creator=False).update(is_viewed_by_creator=True)

        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Siyahını göstərməklə yanaşı sayını da göndəririk
        context['pending_count'] = self.get_queryset().count()
        return context 


@login_required
@require_POST
@csrf_exempt
def approve_split(request, split_id):
        # Təhlükəsizlik: Yalnız xərci yaradan şəxs bu split-i idarə edə bilər
        split = get_object_or_404(
            ExpenseSplit, 
            id=split_id, 
            expense__paid_by=request.user,
            waiting_for_settlement=True
        )
        
        action = request.POST.get  ('action')

        if action == 'approve':
            split.is_settled = True
            split.waiting_for_settlement = False
            split.save()
            return JsonResponse({'status': 'success', 'message': 'Ödəniş təsdiqləndi'})
        
        elif action == 'reject':
            split.is_settled = False
            split.waiting_for_settlement = False
            split.save()
            return JsonResponse({'status': 'success', 'message': 'İmtina edildi'})

        return JsonResponse({'status': 'error', 'message': 'Yanlış əməliyyat'}, status=400)


class BalanceView(LoginRequiredMixin, TemplateView):
    template_name = 'balance.html'

    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     user = self.request.user

    #     # 1. Alacaqlar: Mənim yaratdığım xərclər üzrə hələ ödənilməmiş (is_settled=False) olanlar
    #     receivables = ExpenseSplit.objects.filter(
    #         expense__paid_by=user,
    #         is_settled=False
    #     ).values('user__first_name', 'user__last_name', 'user__username', 'user__id').annotate(
    #         total_amount=Sum('amount_owed')
    #     )

    #     # 2. Borclarım: Başqalarının yaratdığı xərclərdə mənim payıma düşən ödənilməmiş hissələr
    #     debts = ExpenseSplit.objects.filter(
    #         user=user,
    #         is_settled=False
    #     ).exclude(expense__paid_by=user).values(
    #         'expense__paid_by__first_name', 
    #         'expense__paid_by__last_name', 
    #         'expense__paid_by__username',
    #         'expense__paid_by__id'
    #     ).annotate(
    #         total_amount=Sum('amount_owed')
    #     )

    #     context['receivables'] = receivables
    #     context['debts'] = debts
    #     context['total_receivable'] = receivables.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    #     context['total_debt'] = debts.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
    #     return context
    

@csrf_exempt
def register_device(request):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            token = data.get('token')
            device_type = data.get('type', 'web')

            # Əgər bu token artıq varsa yeniləyirik, yoxdursa yaradırıq
            device, created = FCMDevice.objects.get_or_create(
                registration_id=token,
                defaults={'user': request.user, 'type': device_type}
            )
            
            if not created:
                device.user = request.user
                device.save()
                
            return JsonResponse({"status": "success", "message": "Cihaz qeydə alındı."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
    return JsonResponse({"status": "error", "message": "İcazə yoxdur"}, status=403)