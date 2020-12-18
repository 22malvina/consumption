from django.contrib import admin
from .models import Company, Employee

from cheque.models import FNSCheque

#admin.site.register(Company)
admin.site.register(Employee)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
     readonly_fields = ('count_report', 'report')
     def count_report(self, instance):
         if instance.id:
             return FNSCheque.objects.filter(company=instance).count()
         return 0
     def report(self, instance):
         if instance.id:
             return "\n".join(map(lambda x: str(x), FNSCheque.objects.filter(company=instance)[0:1000]))
         return
