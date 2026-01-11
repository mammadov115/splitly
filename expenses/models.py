from django.db import models
from django.contrib.auth.models import User
from django.db import transaction



class Expense(models.Model):
    title = models.CharField(max_length=255) 
    amount = models.DecimalField(max_digits=10, decimal_places=2) 
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_paid')
    split_with = models.ManyToManyField(User, through='ExpenseSplit', related_name='expenses_shared')
    date = models.DateTimeField(auto_now_add=True)
    

    is_split_equally = models.BooleanField(default=True) 

    def __str__(self):
        return f"{self.title} - {self.amount} AZN"
    
    def split_expense(self, users_list):
        """
        users_list: Expense list for spliting the expense equally among given users
        """
        if not users_list:
            return

        split_amount = self.amount / len(users_list)

        # Using transaction to ensure atomicity
        with transaction.atomic():
            # Clear existing splits if any
            self.splits.all().delete()
            
            for user in users_list:
                settled_status = (user == self.paid_by)
                ExpenseSplit.objects.create(
                    expense=self,
                    user=user,
                    amount_owed=split_amount,
                    is_settled=settled_status
                )
        
    @property
    def other_splits(self):
        # Bu funksiya xərci yaradan (ödəyən) adamın payını avtomatik çıxarır
        return self.splits.exclude(user=self.paid_by)
    
    @property
    def my_split(self):
        return self.splits.filter(user=self.paid_by).first()

    def get_type(self, user):
        if self.paid_by == user:
            return "paid_by_me"
        elif self.splits.filter(user=user).exists():
            return "shared_with_me"
        else:
            return "other"

class ExpenseSplit(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2)
    is_settled = models.BooleanField(default=False) 
    waiting_for_settlement = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    is_viewed_by_creator = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.amount_owed}"
    

