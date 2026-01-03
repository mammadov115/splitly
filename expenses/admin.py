from django.contrib import admin
from .models import Expense, ExpenseSplit

# Xərclərin bölünməsi hissəsini Expense-in daxilində göstərmək üçün Inline
class ExpenseSplitInline(admin.TabularInline):
    model = ExpenseSplit
    extra = 1  # Yeni xərc yaradanda avtomatik neçə boş sətir görünsün
    autocomplete_fields = ['user'] # İstifadəçi siyahısı çoxdursa axtarışı asanlaşdırır

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'paid_by', 'date', 'is_split_equally')
    list_filter = ('date', 'paid_by', 'is_split_equally')
    search_fields = ('title', 'paid_by__username')
    inlines = [ExpenseSplitInline]
    date_hierarchy = 'date' # Təqvim üzrə sürətli filtr

@admin.register(ExpenseSplit)
class ExpenseSplitAdmin(admin.ModelAdmin):
    list_display = ('expense', 'user', 'amount_owed')
    list_filter = ('user',)
    search_fields = ('expense__title', 'user__username')