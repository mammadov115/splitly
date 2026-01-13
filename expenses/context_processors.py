from django.db.models import Sum
from expenses.models import ExpenseSplit

def balance_processor(request):
    if request.user.is_authenticated:
        user = request.user

        # 1. Alacaqlar: Mənim yaratdığım xərclər üzrə hələ ödənilməmiş (is_settled=False) olanlar
        receivables = ExpenseSplit.objects.filter(
            expense__paid_by=user,
            is_settled=False
        ).values('user__first_name', 'user__last_name', 'user__username', 'user__id').annotate(
            total_amount=Sum('amount_owed')
        )

        # 2. Borclarım: Başqalarının yaratdığı xərclərdə mənim payıma düşən ödənilməmiş hissələr
        debts = ExpenseSplit.objects.filter(
            user=user,
            is_settled=False
        ).exclude(expense__paid_by=user).values(
            'expense__paid_by__first_name', 
            'expense__paid_by__last_name', 
            'expense__paid_by__username',
            'expense__paid_by__id'
        ).annotate(
            total_amount=Sum('amount_owed')
        )


        total_receivable = receivables.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        total_debt = debts.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        # 3. Xalis Balans (Alacaq - Borc)
        net_balance = total_receivable - total_debt
           

        return {
            'total_receivable': total_receivable,
            'total_debt': total_debt,
            'net_balance': net_balance,
            'receivables': receivables,
            'debts': debts,
        }
    
    return {
        'total_receivable': 0,
        'total_debt': 0,
        'net_balance': 0,
    }