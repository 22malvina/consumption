from django.contrib import admin


from .models import FNSCheque, FNSChequeElement, ShowcasesCategory

#admin.site.register(FNSCheque)
class FNSChequeElementInline(admin.TabularInline):
        model = FNSChequeElement

@admin.register(FNSCheque)
class FNSChequeAdmin(admin.ModelAdmin):
    #list_display = ('title', 'author', 'display_genre')
    inlines = [FNSChequeElementInline]
    search_fields = ['json']


#admin.site.register(FNSChequeElement)
@admin.register(FNSChequeElement)
class FNSChequeElementAdmin(admin.ModelAdmin):
    search_fields = ['name', 'price', 'sum', 'quantity']
    readonly_fields = ['fns_cheque', 'link_to_admin_cheque']

    def link_to_admin_cheque(self, instance):
        if instance.id and instance.fns_cheque:
            #return '<a href="/admin/cheque/fnschequeelement/' + str(instance.fns_cheque.id) + '">' + str(instance.fns_cheque) + '</a>'
            return '/admin/cheque/fnscheque/' + str(instance.fns_cheque.id)
        return ''

admin.site.register(ShowcasesCategory)
