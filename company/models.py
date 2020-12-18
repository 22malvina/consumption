# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models

class Employee(models.Model):
    title = models.CharField(blank=True, max_length=254)
    datetime_create = models.DateTimeField(auto_now_add = True)
    key = models.CharField(blank=True, max_length=254)
    first_name = models.CharField(blank=True, max_length=254)
    last_name = models.CharField(blank=True, max_length=254)
    language_code = models.CharField(blank=True, null=True, max_length=15)
    telegram_id = models.CharField(blank=True, max_length=254)

    def __unicode__(self):
        return u"Employee: %s,  %s, %s, %s" % (self.id, self.title, self.first_name, self.last_name)

class Company(models.Model):
    title = models.CharField(blank=True, max_length=254)
    employees = models.ManyToManyField(Employee)
    datetime_create = models.DateTimeField(auto_now_add = True)
    telegram_chat_id = models.CharField(blank=True, max_length=254)

    def __unicode__(self):
        return u"Company: %s, %s, %s" % (self.id, self.title, self.telegram_chat_id)


