from django.db import models
from django.contrib.auth.models import User
from django.db import transaction



class Expense(models.Model):
    title = models.CharField(max_length=255) 
    amount = models.DecimalField(max_digits=10, decimal_places=2) 
    paid_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_paid')
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
                ExpenseSplit.objects.create(
                    expense=self,
                    user=user,
                    amount_owed=split_amount
                )

class ExpenseSplit(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE, related_name='splits')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2) 

    def __str__(self):
        return f"{self.user.username} - {self.amount_owed}"
    

