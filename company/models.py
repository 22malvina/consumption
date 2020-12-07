# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.


class Employee(models.Model):
    title = models.CharField(blank=True, max_length=254)
    datetime_create = models.DateTimeField(auto_now_add = True)
    key = models.CharField(blank=True, max_length=254)

class Company(models.Model):
    title = models.CharField(blank=True, max_length=254)
#    owner = models.ForeignKey(Employee, blank=True, null=True)
    employees = models.ManyToManyField(Employee)
#    account = models.ForeignKey(Account, blank=True, null=True)
    datetime_create = models.DateTimeField(auto_now_add = True)
#    company = models.CharField(blank=True, max_length=254)
    #showcase = models.ForeignKey(Showcase, blank=True, null=True) # дополнительная информация о витрине на которй осуествили заказ и оплату
#    sum = models.SmallIntegerField(blank=True, null=True)
#    datetime = models.DateTimeField(blank=True, null = True) # дата покупки
    # у ручных чеков этого может не быть
    #   а те что из приехали из ФНС нужно отдельно связь завести что чек уже на онсве JSON создавался и об этом должен помнить создатель чеков.
    #fn = models.CharField(blank=True, max_length=254)
    #fdp = models.CharField(blank=True, max_length=254)
    #fd = models.CharField(blank=True, max_length=254)

#    user_inn = models.CharField(blank=True, max_length=254) # ИНН организации


    #quantity = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=3) # штуки или граммы


