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
from django.db.models import Q, OuterRef, Subquery, Sum
import json
from decimal import Decimal
from django.db import transaction
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from expenses.utils import send_live_notification
from fcm_django.models import FCMDevice
from expenses.utils import log




class HomeView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'home.html'
    context_object_name = 'expenses'
    ordering = ['-date']
    login_url = 'login'
    paginate_by = 5  # Hər səhifədə neçə xərc görünüsn

    def get_queryset(self):
            user = self.request.user
            view_type = self.request.GET.get('view', 'expenses')
            
            # 1. Cari user-in həmin xərcdəki split-ini tapmaq üçün Subquery
            user_shares = ExpenseSplit.objects.filter(
                expense=OuterRef('pk'), 
                user=user
            )

            # 2. Əsas sorğu
            queryset = Expense.objects.filter(
                Q(paid_by=user) | Q(splits__user=user)
            ).select_related('paid_by').prefetch_related('splits__user').annotate(
                my_split_id=Subquery(user_shares.values('pk')[:1]),
                my_share=Subquery(user_shares.values('amount_owed')[:1]),
                is_settled=Subquery(user_shares.values('is_settled')[:1]),
                waiting_for_settlement=Subquery(user_shares.values('waiting_for_settlement')[:1])
            ).distinct()

            # Filter by type
            if view_type == 'payments':
                queryset = queryset.filter(is_payment=True)
            else:
                queryset = queryset.filter(is_payment=False)

            queryset = queryset.order_by('-date')
            
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
        context['current_view'] = self.request.GET.get('view', 'expenses')

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
        is_payment = data.get('is_payment', False)

        if not title or amount <= 0:
            return JsonResponse({'success': False, 'error': 'Məlumatlar tam deyil'}, status=400)

        # 1. Xərci yaradan (Ödəyən hazırkı userdir)
        expense = Expense.objects.create(
            title=title,
            amount=amount,
            paid_by=request.user,
            is_payment=is_payment
        )

        # 2. Xərci bölmək (Əgər heç kim seçilməyibsə, yalnız özünə yazır)
        if not user_ids:
            user_ids = [request.user.id]
        
        users_to_split = User.objects.filter(id__in=user_ids)
        
        # Split logic tailored for payments
        if is_payment:
            split_amount = amount / len(users_to_split)
            for user in users_to_split:
                ExpenseSplit.objects.create(
                    expense=expense,
                    user=user,
                    amount_owed=split_amount,
                    is_settled=False,
                    waiting_for_settlement=True
                )
        else:
            expense.split_expense(users_to_split)
        

        # --- BİLDİRİŞ GÖNDƏRMƏ HİSSƏSİ ---
        notification_title = "Yeni Xərc!"
        log(f"Preparing to send notifications for expense '{title}' to users: {[user.username for user in users_to_split]}")
        
        for user_to_notify in users_to_split:
            # Özümüzə bildiriş göndərmirik
            if user_to_notify != request.user:
                # Hər istifadəçi üçün öz payını tapırıq
                user_split = expense.splits.filter(user=user_to_notify).first()
                split_amount_str = f"{user_split.amount_owed} ₼" if user_split else "0 ₼"
                notification_body = f"{request.user.username} '{title}' qeyd etdi. Sənin payın: {split_amount_str}"

                # 1. Firebase Live Push Notification
                try:
                    send_live_notification(
                        user=user_to_notify,
                        title=notification_title,
                        body=notification_body
                    )
                except Exception as fcm_error:
                    log(f"FCM Error for {user_to_notify.username}: {fcm_error}")

        # 3. Yeni statusu göndərmək
        return HttpResponse(status=200)

    except Exception as e:
        log(f"AJAX Error in add_expense_ajax: {str(e)}")
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
        # Yalnız cari istifadəçinin yaratdığı xərclər üzrə digərlərinin təsdiq gözləyən splitlər (Pay Now flow)
        # VƏ Cari istifadəçiyə başqası tərəfindən edilən ödənişlər (Payment flow)
        qs = ExpenseSplit.objects.filter(
            Q(expense__paid_by=self.request.user, expense__is_payment=False, waiting_for_settlement=True) |
            Q(user=self.request.user, expense__is_payment=True, waiting_for_settlement=True)
        ).exclude(user=self.request.user, expense__is_payment=False).select_related('expense', 'user', 'expense__paid_by').order_by('-id')

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
        # Təhlükəsizlik: Yalnız xərci yaradan şəxs VƏ YA ödənişi qəbul edən şəxs bu split-i idarə edə bilər
        split = get_object_or_404(
            ExpenseSplit, 
            Q(id=split_id, expense__paid_by=request.user) | Q(id=split_id, user=request.user, expense__is_payment=True),
            waiting_for_settlement=True
        )
        
        action = request.POST.get('action')

        if action == 'approve':
            # Ödəniş və ya xərc spliti təsdiqlənir
            if split.expense.is_payment:
                # Ödəniş qəbul olundusa, artıq balansda rəsmən nəzərə alınır
                # is_settled-i False saxlayırıq ki, netting logic-də iştirak etsin
                split.waiting_for_settlement = False
            else:
                # Köhnə "Pay Now" logic-i üçün
                split.is_settled = True
                split.waiting_for_settlement = False
            
            split.save()
            return JsonResponse({'status': 'success', 'message': 'Əməliyyat təsdiqləndi'})
        
        elif action == 'reject':
            split.waiting_for_settlement = False
            # Əgər ödənişdirsə, bəlkə də silmək daha məntiqlidir? 
            # Amma hələlik sadəcə waiting statusundan çıxarırıq.
            split.save()
            return JsonResponse({'status': 'success', 'message': 'İmtina edildi'})

        return JsonResponse({'status': 'error', 'message': 'Yanlış əməliyyat'}, status=400)


class BalanceView(LoginRequiredMixin, TemplateView):
    template_name = 'balance.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # 1. Alacaqlar: Others owe me (I paid, they haven't settled)
        receivables_qs = ExpenseSplit.objects.filter(
            expense__paid_by=user,
            is_settled=False,
            waiting_for_settlement=False
        ).exclude(user=user).values(
            'user__id', 'user__first_name', 'user__last_name', 'user__username'
        ).annotate(total_amount=Sum('amount_owed'))

        # 2. Borclarım: I owe others (They paid, I haven't settled)
        debts_qs = ExpenseSplit.objects.filter(
            user=user,
            is_settled=False,
            waiting_for_settlement=False
        ).exclude(expense__paid_by=user).values(
            'expense__paid_by__id', 'expense__paid_by__first_name', 'expense__paid_by__last_name', 'expense__paid_by__username'
        ).annotate(total_amount=Sum('amount_owed'))

        # Netting logic
        user_balances = {}

        # Process receivables (positive balance)
        for r in receivables_qs:
            uid = r['user__id']
            user_balances[uid] = {
                'id': uid,
                'first_name': r['user__first_name'],
                'last_name': r['user__last_name'],
                'username': r['user__username'],
                'amount': r['total_amount']
            }

        # Substract debts (negative balance)
        for d in debts_qs:
            uid = d['expense__paid_by__id']
            if uid in user_balances:
                user_balances[uid]['amount'] -= d['total_amount']
            else:
                user_balances[uid] = {
                    'id': uid,
                    'first_name': d['expense__paid_by__first_name'],
                    'last_name': d['expense__paid_by__last_name'],
                    'username': d['expense__paid_by__username'],
                    'amount': -d['total_amount']
                }

        final_receivables = []
        final_debts = []
        total_receivable = Decimal('0')
        total_debt = Decimal('0')

        for uid, data in user_balances.items():
            if data['amount'] > 0:
                final_receivables.append({
                    'user__id': data['id'],
                    'user__first_name': data['first_name'],
                    'user__last_name': data['last_name'],
                    'user__username': data['username'],
                    'total_amount': data['amount']
                })
                total_receivable += data['amount']
            elif data['amount'] < 0:
                final_debts.append({
                    'expense__paid_by__id': data['id'],
                    'expense__paid_by__first_name': data['first_name'],
                    'expense__paid_by__last_name': data['last_name'],
                    'expense__paid_by__username': data['username'],
                    'total_amount': abs(data['amount'])
                })
                total_debt += abs(data['amount'])

        context['receivables'] = final_receivables
        context['debts'] = final_debts
        context['total_receivable'] = total_receivable
        context['total_debt'] = total_debt
        
        # Unified balances list for the "merged" section in balance.html
        balances_list = []
        for uid, data in user_balances.items():
            if data['amount'] != 0:
                balances_list.append({
                    'id': uid,
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'username': data['username'],
                    'amount': data['amount'],
                    'abs_amount': abs(data['amount']),
                })
        # Sort by absolute amount descending
        balances_list.sort(key=lambda x: x['abs_amount'], reverse=True)
        context['balances'] = balances_list

        # Additional context for modal and navbar
        context['all_users'] = User.objects.exclude(id=user.id).exclude(is_superuser=True)
        context['has_new_notifications'] = ExpenseSplit.objects.filter(
            expense__paid_by=user, 
            waiting_for_settlement=True,
            is_viewed_by_creator=False
        ).exists()
        
        return context
    

@login_required
@require_POST
def update_expense_ajax(request, expense_id):
    try:
        expense = get_object_or_404(Expense, id=expense_id, paid_by=request.user)
        data = json.loads(request.body)
        
        title = data.get('title')
        amount = Decimal(str(data.get('amount')))
        user_ids = data.get('split_with', [])

        if not title or amount <= 0:
            return JsonResponse({'success': False, 'error': 'Məlumatlar tam deyil'}, status=400)

        with transaction.atomic():
            expense.title = title
            expense.amount = amount
            expense.save()

            if not user_ids:
                user_ids = [request.user.id]
            
            users_to_split = User.objects.filter(id__in=user_ids)
            expense.split_expense(users_to_split)

        return HttpResponse(status=200)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_POST
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, paid_by=request.user)
    expense.delete()
    return JsonResponse({'status': 'success', 'message': 'Xərc silindi'})


@csrf_exempt
def register_device(request):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            token = data.get('token')
            device_type = data.get('type', 'web')

            # Əgər bu token artıq varsa yeniləyirik, yoxdursa yaradırıq
            device, created = FCMDevice.objects.get_or_create(
                user=request.user,
                type=device_type,
                defaults={'registration_id': token, 'active': True}
            )
            print(f"Device registration: {device}, Created: {created}")
             # Əgər cihaz artıq mövcuddursa, istifadəçini yeniləyirik
            
            if not created:
                device.user = request.user
                device.save()
                
            return JsonResponse({"status": "success", "message": "Cihaz qeydə alındı."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
    
    return JsonResponse({"status": "error", "message": "İcazə yoxdur"}, status=403)