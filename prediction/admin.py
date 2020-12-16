from django.contrib import admin

from .models import PredictionLinearFunction
from cheque.models import FNSChequeElement

#class PredictionLinearFunctionTOFNSChequeElementInline(admin.TabularInline):
#    model = PredictionLinearFunction.cheque_elements.through
#    exclude = ('fns_cheque',)

@admin.register(PredictionLinearFunction)
class PredictionLinearFunctionAdmin(admin.ModelAdmin):
#    inlines = [PredictionLinearFunctionTOFNSChequeElementInline]
     exclude = ('cheque_elements',)
     search_fields = ['json', 'cheque_elements']
     readonly_fields = ('count_report', 'report')
     def count_report(self, instance):
         if instance.id:
             return len(instance.cheque_elements.all())
         return 0
     def report(self, instance):
         if instance.id:
             s = []
             for i in instance.cheque_elements.all():
                 s.append(str(i))
             return "\n".join(s)
         return
