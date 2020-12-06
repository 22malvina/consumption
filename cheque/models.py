# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class ChequeFNS(models.Model):
#    account = models.ForeignKey(Account, blank=True, null=True)
    #datetime_create = models.DateTimeField(blank=True, auto_now_add = True)
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

    fns_fiscalDocumentNumber = models.CharField(blank=True, max_length=254)
    fns_fiscalDriveNumber = models.CharField(blank=True, max_length=254)
    fns_fiscalSign = models.CharField(blank=True, max_length=254)

    fns_dateTime = models.CharField(blank=True, max_length=254)
    fns_totalSum = models.CharField(blank=True, max_length=254)

    def is_shop_SPAR(self):
        if self.user_inn == "5258056945":
            return True
        return False

    def get_datetime(self):
        return self.fns_dateTime

class ChequeFNSElement(models.Model):
    """
    нужно учитывать весовой товар
    цена за штуку
    {"quantity":2,"sum":11980,"price":5990,"name":"4607045982771 МОЛОКО SPAR УЛЬТРАПА"}
    {"quantity":0.205,"sum":7770,"price":37900,"name":"259 АВОКАДО ВЕСОВОЕ"}

    {"weight": 220, "quantity":1,"sum":13500,"price":13500,"name":u"4607004891694 СЫР СЛИВОЧНЫЙ HOCHLA", "volume": 0.22},
    """
    cheque_fns = models.ForeignKey(ChequeFNS)
    name = models.CharField(blank=True, null=True, max_length=254)
#    price = models.SmallIntegerField(blank=True, null=True) # цена за штуку или за 1000 грамм
    #quantity = models.SmallIntegerField(blank=True, null=True) # штуки или граммы
    quantity = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=3) # штуки или граммы

#    sum = models.SmallIntegerField(blank=True, null=True) # финальная цена
#    product_info = models.ForeignKey(ProductInfo, blank=True, null=True) # дополнительная информация о продукте полученная из иногог источника и обогазенная с целью облегчить жизнь пользователю не вбивать данные по прдуктам
    #extended_product_info_manual = models.ForeignKey(ExtendedProductInfoManual, blank=True, null=True)
    # можно было бы добавить фото куленного продукта
    # среию продукта
    # срок годности(гаарантийный срок)
    # дата производства

    # пользователь сам указывает по данной позиции этот параметр
    volume = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=3) # указываем 1 если весовой товар или вес одной штуки в килошраммах
    

#    def get_barcode(self):
#        if self.has_barcode():
#            if self.cheque_fns.is_shop_SPAR():
#                return self.name.split()[0]
#                #return self.product_info.title.split()[0]
#        assert False
#
#    def get_price(self):
#        return self.price
#
#    def get_quantity(self):
#        return self.quantity
#
#    def get_sum(self):
#        return self.sum
#
    def get_title(self):
        return self.name
#
#    def has_barcode(self):
#        if self.cheque_fns.is_shop_SPAR():
#            if len(self.name.split()[0]) == 13:
#            #if len(self.product_info.title.split()[0]) == 13:
#                return True
#        return False

    def consumption_element_params(self):
        return {
            'title': self.get_title(),
            'datetime': self.cheque_fns.get_datetime(),
            'weight': float(self.volume * self.quantity),
        }


    def __str__(self):
        #return "%s %s %s %s" % (str(self.price), self.product_card, str(self.datetime), self.showcase.encode('utf8'))
        #return "%s %s %s" % (str(self.price), str(self.datetime), self.showcase)
        return u"%s %s %s" % (str(self.name), str(self.quantity), self.volume) 
 
