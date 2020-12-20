# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from company.models import Company

import time
import json
import urllib
import urllib2, base64

import re

import ast # нужен для того чтобы из сохраненного как бы джисона достать данные

"""
json чека ипортированного из ФНС России
место хранения

t=20200603T145000&s=3390.59&fn=9282440300628259&i=2031&fp=2548611914&n=1

{
    "document": {
        "receipt": {
            "ecashTotalSum":339059,
            "fiscalDriveNumber":"9282440300628259",
            "retailPlaceAddress":"107076, г.Москва, ул.Богородский Вал, д.6, корп.2",
            "fiscalDocumentNumber":2031,
            "taxationType":1,
            "shiftNumber":8,
            "userInn":"5258056945",
            "operationType":1,
            "receiptCode":3,
            "items":[
                {
                    "price":2990,
                    "name":"240 КАРТОФЕЛЬ",
                    "quantity":1.93,
                    "sum":5771
                },
                {"price":5990,"name":"4607045982771 МОЛОКО SPAR УЛЬТРАПА","quantity":3,"sum":17970},
                {"price":5990,"name":"7622210736970 ШОКОЛАД MILKA МОЛОЧН","quantity":1,"sum":5990},
            ],
            "user":"ООО \"Спар Миддл Волга\"",
            "fiscalSign":2548611914,
            "dateTime":"2020-06-03T14:50:00",
            "requestNumber":8,
            "totalSum":339059,
            "nds10":22252,
            "rawData": "",
            "nds18":15718,
            "cashTotalSum":0,
            "kktRegId":"0001732259050091    ",
            "operator":"Усикова Дарья Игорев"
        }
    }
}
"""

class ShowcasesCategory(models.Model):
    """
    Катигории витрин которые реализуют продукцию
    Гипермаркет, Финансовые операции, Кафе и рестораны, Мобильная связь, Общественный транспорт, Одежда и обувь, Отпуск и путешествия, Медицина и аптеки, Красота и здоровье
    """
    title = models.CharField(blank=True, max_length=254)

    def __unicode__(self):
        return self.title

class FNSCheque(models.Model):
    json = models.TextField(blank=True, )
    company = models.ForeignKey(Company, blank=True, null=True) #TODO чек простой элемент и компанию надо вынести из чека
    showcases_category = models.ForeignKey(ShowcasesCategory, blank=True, null=True) #TODO чек простой элемент и категорию витрины на которй он был пробит надо убрать

#    datetime_create = models.DateTimeField(blank=True, auto_now_add = True)
    fns_userInn = models.CharField(blank=True, max_length=254) # ИНН организации

    #t=20200523T2158&s=3070.52&fn=9289000100405801&i=69106&fp=3872222871&n=1
    fns_fiscalDocumentNumber = models.CharField(blank=True, max_length=254) #FD i ФД
    fns_fiscalDriveNumber = models.CharField(blank=True, max_length=254) #FN fn ФН
    fns_fiscalSign = models.CharField(blank=True, max_length=254) #FDP fp ФП

    fns_dateTime = models.CharField(blank=True, max_length=254) #date t
    fns_totalSum = models.CharField(blank=True, max_length=254) #sum s

    # ручно режим
    is_manual = models.BooleanField() # если выставлено то значит ручная тарат
    #manual_how_much = models.CharField(blank=True, max_length=254) # используем fns_totalSum
    manual_what = models.CharField(blank=True, max_length=254)
    manual_where = models.CharField(blank=True, max_length=254)
    #manual_when = models.CharField(blank=True, max_length=254) # используем fns_dateTime чтобы сортировать

    @classmethod
    def change_showcases_category(self, company, cheque_id, showcases_category_id):
        cheque = FNSCheque.objects.get(company=company, id=cheque_id)
        showcases_category = ShowcasesCategory.objects.get(id=showcases_category_id)
        cheque.showcases_category = showcases_category
        cheque.save()

    @classmethod
    def create_and_save_cheque_from_text(cls, company, p0, p1, p2, p3):
	c = FNSCheque(is_manual=True, company=company, fns_totalSum=p0, manual_what=p1, manual_where=p2, fns_dateTime=p3)
        c.save()
        return c
        
    @classmethod
    def create_fns_cheque_from_qr_text(cls, qr_text, company):
        if cls.has_cheque_with_qr_text(company, qr_text):
            #Такой чек уже существует'
            print u'Alert: We has this cheque in this company!'
            assert False
	qr_params = QRCodeReader.qr_text_to_params(qr_text)
        if len(qr_params.keys()) != 5:
            assert False
	cheque_params = QRCodeReader.qr_params_to_cheque_params(qr_params)
	return FNSCheque(is_manual=False, company=company, fns_fiscalDocumentNumber=cheque_params['fns_fiscalDocumentNumber'], fns_fiscalDriveNumber=cheque_params['fns_fiscalDriveNumber'], fns_fiscalSign=cheque_params['fns_fiscalSign'], fns_dateTime=cheque_params['fns_dateTime'], fns_totalSum=cheque_params['fns_totalSum'])

    @classmethod
    def create_save_update_fns_cheque_from_proverkacheka_com(cls, qr_text, company):
	fns_cheque = FNSCheque.create_fns_cheque_from_qr_text(qr_text, company)
        #TODO проверить что такого чека еще нет в этой окмпании а то получается 2 раза один и тот же чек добавить
	fns_cheque.save()
        fns_cheque_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params('', qr_text)
	#FNSCheque.update_cheque_from_json(fns_cheque, fns_cheque_json)
	fns_cheque.update_cheque_from_json(fns_cheque_json)
        return fns_cheque

    @classmethod
    def find_cheques_in_company_with_inn(cls, company, user_inn):
        return list(FNSCheque.objects.filter(company=company, fns_userInn=user_inn))

    @classmethod
    def find_cheques_in_company_with_user(cls, company, user):
        cheques = []
        for c in FNSCheque.objects.filter(company=company):
            if user == c.get_user():
                cheques.append(c)
        return cheques

    def format_date_qr_srt(self):
        #return str(self.fns_dateTime[0:4]) + str(self.fns_dateTime[5:7]) + str(self.fns_dateTime[8:10]) + 'T' + str(self.fns_dateTime[11:13]) + str(self.fns_dateTime[14:16]) 
        return str(self.fns_dateTime[8:10]) + str(self.fns_dateTime[5:7]) + str(self.fns_dateTime[0:4]) + 'T' + str(self.fns_dateTime[11:13]) + str(self.fns_dateTime[14:16]) 

    def format_sum_qr_srt(self):
        return str(self.fns_totalSum[0:-2]) + '.' + str(self.fns_totalSum[-2:])

    def get_address(self):
        if self.is_manual:
            return self.manual_where

        #add = self.fns_cheque.json["document"]["receipt"]["retailAddress"]
        #add = self.fns_cheque.json['json']["retailAddress"]
        #add = ast.literal_eval(json.loads(self.fns_cheque.json))['json']

        #addd = self.fns_cheque.json

        #if not self.fns_cheque.json or not ast.literal_eval(self.fns_cheque.json).has_key('data'):
        if not self.json or not ast.literal_eval(self.json).has_key('data'):
        #if not self.json or not json.loads(self.json).has_key('data'):
            print 'Error: not find json or json["data"]'
            return
        
        #addd = ast.literal_eval(self.fns_cheque.json)['data']['json']
        addd = ast.literal_eval(self.json)['data']['json']
        #'retailAddress', u'buyerPhoneOrAddress',  retailPlaceAddress
        k = 0
        if addd.has_key('retailPlaceAddress'):
            k += 1
            #print '--1'
        if addd.has_key('retailAddress'):
            k += 1
            #print '--2'
        #if addd.has_key(u'buyerPhoneOrAddress') and addd.get('buyerPhoneOrAddress') not in ['', 'k.a.vakulin@mail.ru', 'l.krylova@muz-lab.ru','yuriy_per@yahoo.com']:
        #    k += 1
        #    print '--3'

        if k > 1:
            #print addd.keys()
            #print addd.get('retailPlaceAddress', '').encode('utf8')
            #print addd.get('retailAddress', '').encode('utf8')
            #print addd.get('buyerPhoneOrAddress', '').encode('utf8')
            #print '----'
            assert False

        if addd.has_key('retailPlaceAddress'):
            add = addd['retailPlaceAddress']
        elif addd.has_key('retailAddress'):
            add = addd['retailAddress']
        #elif addd.has_key(u'buyerPhoneOrAddress'):
        #    add = addd[u'buyerPhoneOrAddress']
        else:
            #print '+++ k=', k
            #print addd.get(u'buyerPhoneOrAddress')
            #print addd.keys()
            add = ''
            #assert False
        #add = addd['json']
#        print add.encode('utf8')
        #get_retailAddress
        return add

    @classmethod
    def get_cheque_with_qr_text(cls, company, qr_text):
	qr_params = QRCodeReader.qr_text_to_params(qr_text)
        if len(qr_params.keys()) != 5:
            assert False
	cheque_params = QRCodeReader.qr_params_to_cheque_params(qr_params)

        fiscalDocumentNumber = cheque_params['fns_fiscalDocumentNumber']
        fiscalDriveNumber = cheque_params['fns_fiscalDriveNumber']
        fiscalSign = cheque_params['fns_fiscalSign']
        dateTime = cheque_params['fns_dateTime']
        totalSum = cheque_params['fns_totalSum']

        return FNSCheque.objects.get(
            company=company,
            fns_fiscalDocumentNumber=fiscalDocumentNumber,
            fns_fiscalDriveNumber=fiscalDriveNumber,
            fns_fiscalSign=fiscalSign,
            fns_dateTime__contains=dateTime,
            fns_totalSum=totalSum)

    @classmethod
    def get_cheque_with_fns_cheque_json(cls, company, fns_cheque_json):
        fiscalDocumentNumber = fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"]
        fiscalDriveNumber = fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"]
        fiscalSign = fns_cheque_json["document"]["receipt"]["fiscalSign"]
        dateTime = fns_cheque_json["document"]["receipt"]["dateTime"]
        totalSum = fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')

        return FNSCheque.objects.get(
            company=company,
            fns_fiscalDocumentNumber=fiscalDocumentNumber,
            fns_fiscalDriveNumber=fiscalDriveNumber,
            fns_fiscalSign=fiscalSign,
            fns_dateTime__contains=dateTime,
            fns_totalSum=totalSum)

    def get_datetime(self):
        return self.fns_dateTime

    def get_operator(self):
        if not self.json or not ast.literal_eval(self.json).has_key('data'):
            print 'Error: not find json or json["data"]'
            return
        
        addd = ast.literal_eval(self.json)['data']['json']
        k = 0
        if addd.has_key('operator'):
            k += 1

        if k > 1:
            assert False

        if addd.has_key('operator'):
            add = addd['operator']
        else:
            add = ''
        return add

    def get_recomended_showcases_category(self):
        inn_cheques = FNSCheque.find_cheques_in_company_with_inn(self.company, self.get_user_inn())
        user_cheques = FNSCheque.find_cheques_in_company_with_user(self.company, self.get_user())
        scs = {}
        for c in inn_cheques + user_cheques:
            if c.showcases_category:
                if not scs.has_key(c.showcases_category):
                    scs[c.showcases_category] = 0
                scs[c.showcases_category] += 20

        for company in Company.objects.filter(employees__in=self.company.employees.all()): 
            inn_cheques = FNSCheque.find_cheques_in_company_with_inn(company, self.get_user_inn())
            user_cheques = FNSCheque.find_cheques_in_company_with_user(company, self.get_user())
            for c in inn_cheques + user_cheques:
                if c.showcases_category:
                    if not scs.has_key(c.showcases_category):
                        scs[c.showcases_category] = 0
                    scs[c.showcases_category] += 1

        if len(scs.keys()) == 0:
            if ShowcasesCategory.objects.count() > 0 and ShowcasesCategory.objects.filter(id=1).count() > 0:
                return ShowcasesCategory.objects.get(id=1)
            else:
                print 'Alert: Only for test!'
                return ShowcasesCategory(title='Time test', id=1)

        sort_scs = sorted(scs.items(), key=lambda x : x[1])

        best_category = sort_scs[-1][0]
        return best_category

        #if ShowcasesCategory.objects.count():
        #    return ShowcasesCategory.objects.get(id=1)
        #else:
        #    print 'Alert: Only for test!'
        #    return ShowcasesCategory(title='Time test', id=1)

    def get_shop_short_info_string(self):
        if self.get_user():
            return self.get_user()
        elif self.get_address():
            return self.get_address()
        elif self.get_user_inn():
            #return 'ИНН ' + self.get_user_inn() + ' ' + self.get_operator()
            return self.get_user_inn()
        else:
            return

    def get_shop_info_string(self):
        return 'МАГАЗИН: ' + self.get_user() + ' ИНН: ' + self.get_user_inn() + ' АДРЕС: ' + self.get_address()

    def get_user(self):
        if not self.json or not ast.literal_eval(self.json).has_key('data'):
            print 'Error: not find json or json["data"]'
            return
        
        addd = ast.literal_eval(self.json)['data']['json']
        k = 0
        if addd.has_key('user'):
            k += 1

        if k > 1:
            assert False

        if addd.has_key('user'):
            add = addd['user']
        else:
            add = ''
        return add

    def get_user_inn(self):
        return self.fns_userInn

    @staticmethod
    def import_from_proverkacheka_com_format_like_fns(qr_text, company):
        qr_params = QRCodeReader.qr_text_to_params(qr_text)
        if len(qr_params.keys()) != 5:
            print 'Error: Not enough params'
            return
        #fns_cheque_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params(cheque)
        fns_cheque_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params(qr_params, qr_text)

        if not fns_cheque_json:
            print 'Error: not good json!'
            return

        #if FNSCheque.has_cheque_with_fiscal_params(company,  
        #    fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"],
        #    fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"],
        #    fns_cheque_json["document"]["receipt"]["fiscalSign"],
        #    fns_cheque_json["document"]["receipt"]["dateTime"],
        #    fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')):
        #    print u'Alert: We has this cheque!'
        #    #Такой чек уже существует'
        #    return
        if FNSCheque.has_cheque_with_fns_cheque_json(company, fns_cheque_json):
            return

        FNSCheque.save_cheque_from_fns_cheque_json(company, fns_cheque_json)

    @classmethod
    def has_cheque_with_fiscal_params(cls, company, fiscalDocumentNumber, fiscalDriveNumber, fiscalSign, dateTime, totalSum):
        for cheque in FNSCheque.objects.filter(
            company=company,
            fns_fiscalDocumentNumber=fiscalDocumentNumber,
            fns_fiscalDriveNumber=fiscalDriveNumber,
            fns_fiscalSign=fiscalSign,
            fns_dateTime__contains=dateTime,
            fns_totalSum=totalSum):
            print '---has cheque----------'
            print cheque
            return True
        return False

    @classmethod
    def has_cheque_with_qr_text(cls, company, qr_text):
	qr_params = QRCodeReader.qr_text_to_params(qr_text)
        if len(qr_params.keys()) != 5:
            assert False
	cheque_params = QRCodeReader.qr_params_to_cheque_params(qr_params)
        return FNSCheque.has_cheque_with_params(company, cheque_params)

    @classmethod
    def has_cheque_with_params(cls, company, cheque_params):
        return FNSCheque.has_cheque_with_fiscal_params(company, 
            cheque_params['fns_fiscalDocumentNumber'],
            cheque_params['fns_fiscalDriveNumber'],
            cheque_params['fns_fiscalSign'],
            cheque_params['fns_dateTime'],
            cheque_params['fns_totalSum'])

    @classmethod
    def has_cheque_with_fns_cheque_json(cls, company, fns_cheque_json):
        if FNSCheque.has_cheque_with_fiscal_params(company,  
            fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"],
            fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"],
            fns_cheque_json["document"]["receipt"]["fiscalSign"],
            fns_cheque_json["document"]["receipt"]["dateTime"],
            fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')):
            print u'Alert: We has this cheque!'
            #Такой чек уже существует'
            return True
        return False

    @classmethod
    def save_cheque_from_fns_cheque_json(cls, company, fns_cheque_json):
        """
        fix надо разделить на три метода:
            1 сохраннеие в базу
            2 создать(если такого еще нет) товары на основе имеющихся продуктов
            2 привязка к позиции в чеке товарв
        """
        if not fns_cheque_json:
            return 

        account = None
        #if cls.has_cheque_with_fiscal_params(company,
        #    fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"],
        #    fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"],
        #    fns_cheque_json["document"]["receipt"]["fiscalSign"],
        #    fns_cheque_json["document"]["receipt"]["dateTime"],
        #    fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')):
        #    print u'Alert: Find same cheque!'
        #    assert False
        if cls.has_cheque_with_fns_cheque_json(company, fns_cheque_json):
            assert False

        # везде добавил временуж зону Москва timezone
        datetime_buy = fns_cheque_json["document"]["receipt"]["dateTime"] + '+03:00'

        #fns_cheque = FNSCheque(
        #    company=company,
        #    json=fns_cheque_json,
        #    fns_userInn=fns_cheque_json["document"]["receipt"]["userInn"],
        #    fns_dateTime=datetime_buy
        #)
        fns_cheque = FNSCheque()
        fns_cheque.company = company
        fns_cheque.fns_dateTime = datetime_buy
        fns_cheque.is_manual = False
        fns_cheque.save()

        #cls.update_cheque_from_json(fns_cheque, fns_cheque_json)
        fns_cheque.update_cheque_from_json(fns_cheque_json)

    #@classmethod
    #def update_cheque_from_json(cls, fns_cheque, fns_cheque_json):
    def update_cheque_from_json(self, fns_cheque_json):
        #fns_cheque.json = fns_cheque_json
        self.json = fns_cheque_json
        #fns_cheque.fns_userInn = fns_cheque_json["document"]["receipt"]["userInn"]
        self.fns_userInn = fns_cheque_json["document"]["receipt"]["userInn"]

        #fns_cheque.fns_fiscalDocumentNumber = fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"]
        #fns_cheque.fns_fiscalDriveNumber = fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"]
        #fns_cheque.fns_fiscalSign = fns_cheque_json["document"]["receipt"]["fiscalSign"]
        #fns_cheque.fns_dateTime = fns_cheque_json["document"]["receipt"]["dateTime"]
        #fns_cheque.fns_totalSum = fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')
        self.fns_fiscalDocumentNumber = fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"]
        self.fns_fiscalDriveNumber = fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"]
        self.fns_fiscalSign = fns_cheque_json["document"]["receipt"]["fiscalSign"]
        self.fns_dateTime = fns_cheque_json["document"]["receipt"]["dateTime"]
        self.fns_totalSum = fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')

        #fns_cheque.save()
        self.save()

        for elemnt in fns_cheque_json["document"]["receipt"].get("items", []):
            #Сначало можно попытаться найти найти товар с таким же названием и пустыми поялми чтобы лишний раз не делать одно и тоже
            #fns_cheque_element = FNSChequeElement(
            #    fns_cheque=fns_cheque,
            #    quantity=elemnt.get("quantity"),
            #    name=elemnt.get("name"),
            #    price=elemnt.get("price"),
            #    sum=elemnt.get("sum"),
            #)
            #fns_cheque_element.save()

            try:
                #fns_cheque_element = FNSChequeElement(
                #    fns_cheque=fns_cheque,
                #    quantity=elemnt.get("quantity"),
                #    name=elemnt.get("name"),
                #    price=elemnt.get("price"),
                #    sum=elemnt.get("sum"),
                #)
                fns_cheque_element = FNSChequeElement(
                    fns_cheque=self,
                    quantity=elemnt.get("quantity"),
                    name=elemnt.get("name"),
                    price=elemnt.get("price"),
                    sum=elemnt.get("sum"),
                )
                fns_cheque_element.save()
            except:
                import traceback
                traceback.print_exc()
                #traceback.print_exception()
                import sys
                print sys.exc_info()
                traceback.print_exception(*sys.exc_info())
                #traceback.print_stack()
                print '------------'

    def __unicode__(self):
        return u"FNSCheque = FDN: %s, FD: %s, FS: %s, DT: %s, TS: %s" % (self.fns_fiscalDocumentNumber, self.fns_fiscalDriveNumber, self.fns_fiscalSign, self.fns_dateTime, self.fns_totalSum)

class FNSChequeElement(models.Model):
    """
    нужно учитывать весовой товар
    цена за штуку
    {"quantity":2,"sum":11980,"price":5990,"name":"4607045982771 МОЛОКО SPAR УЛЬТРАПА"}
    {"quantity":0.205,"sum":7770,"price":37900,"name":"259 АВОКАДО ВЕСОВОЕ"}

    {"weight": 220, "quantity":1,"sum":13500,"price":13500,"name":u"4607004891694 СЫР СЛИВОЧНЫЙ HOCHLA", "volume": 0.22},
    """
    fns_cheque = models.ForeignKey(FNSCheque)
    name = models.CharField(blank=True, null=True, max_length=254)
    price = models.SmallIntegerField(blank=True, null=True) # цена за штуку или за 1000 грамм
    quantity = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=3) # штуки или граммы
    sum = models.SmallIntegerField(blank=True, null=True) # финальная цена

    # пользователь сам указывает по данной позиции этот параметр
    volume = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=3) # указываем 1 если весовой товар или вес одной штуки в килошраммах

    def consumption_element_params(self):
        #if self.volume * self.quantity != self.get_weight_from_title():
        #    print self.volume * self.quantity, '!=', self.get_weight_from_title()
        #if float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))) != self.get_weight_from_title():
        #    print float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))), '!=', self.get_weight_from_title()

        #print 'weight:',
        #print self.volume * self.quantity,
        #print float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))),
        #print self.get_weight_from_title()
        return {
            'title': self.get_title(),
            'datetime': self.fns_cheque.get_datetime(),
            #'weight': float(self.volume * self.quantity),
            'weight': self.get_weight(),
        }

    def get_address(self):
        return self.fns_cheque.get_address()


    def get_datetime(self):
        return self.fns_cheque.get_datetime()

    def get_price(self):
        #return self.price * self.quantity
        return self.price

    def get_quantity(self):
        #print type(self.quantity)
        return int(self.quantity) if self.quantity == int(self.quantity) else self.quantity

    def get_sum(self):
        return self.sum

    def get_price_per_one_gram(self):
        if int(self.price * self.quantity) != int(self.sum):
            print 'Error: price * quantity != sum.',self.price * float(self.quantity), '!=', self.sum
        if not self.get_weight():
            return None
        return float("{0:.2f}".format(self.price * float(self.quantity) / self.get_weight()))

    def get_title(self):
        return self.name

    def get_weight(self):
        if self.__has_weight_from_title() and self.volume:
            if float(self.__get_weight_from_title()) == float(self.volume):
                return float(self.volume * self.quantity)
            else:
                print 'Error: Not rigth weight!'
                assert False
        elif self.__has_weight_from_title():
            return float(self.__get_weight_from_title() * float(self.quantity))
        elif self.volume:
            return float(self.volume * self.quantity)
        else:
            print 'Error: Not have weight!'
            return None
            assert False
            return float(self.quantity)

    def get_weight_from_title(self):
        """
        только для тестов
        """
        print 'Alert: only in test!'
        return self.__get_weight_from_title()

    def __get_weight_from_title(self):
        #1кг 0.224 None
        #Сыр ЛЕБЕДЕВСКАЯ АФ Кавказский по-домашнему мягкий бзмж 45% 300г 1.000 None
        #LAYS Из печи Чипсы карт нежн сыр с 2.000 None
        #Чипсы LAY'S Sticks Сыр чеддер 125г 1.000 None
        return float("{0:.3f}".format(IsPackedAndWeight.weight_from_cheque_title(self.name) / 1000))

    def has_weight_from_title(self):
        """
        только для тестов
        """
        print 'Alert: only in test!'
        return self.__has_weight_from_title()

    def __has_weight_from_title(self):
        #return False if IsPackedAndWeight.weight_from_cheque_title(self.name) == 0 else True
        return IsPackedAndWeight.has_weight_from_cheque_title(self.name)

    def offer_element_params(self):
        #print self.get_title().encode('utf8'), self.fns_cheque.get_datetime(), self.sum, self.volume, self.quantity
        #if self.volume * self.quantity != self.get_weight_from_title():
        #    print self.volume * self.quantity, '!=', self.get_weight_from_title()
        #if float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))) != self.get_weight_from_title():
        #    print float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))), '!=', self.get_weight_from_title()

        #print 'weight:',
        #print self.volume * self.quantity,
        #print float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))),
        #print self.get_weight_from_title()
        return {
            'title': self.get_title(),
            'datetime': self.fns_cheque.get_datetime(),
            #'weight': float(self.volume * self.quantity),
            #'weight': self.get_weight(),
            #'price_per_weight': float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))),
            'price_per_weight': float("{0:.3f}".format(self.sum / self.get_weight())),
        }

    def __str__(self):
        return (self.name.encode('utf8') if self.name else '') + str(' ') + str(self.quantity) + str(' ') + str(self.volume) + str(' ') + str(self.sum) + str(' ') + str(self.price)# + self.name.encode('utf8') 
 
class QRCodeReader(object):
    @classmethod
    def is_it_qr_text(cls, text):
        el = text.split('&')
        if len(el) < 5 or len(el) > 9:
            return False
        for e in el:
            if len(e.split('=')) != 2:
                return False

        cheque = {}
        for e in text.split('&'):
            k, v = e.split('=')
            if k == 't':
                cheque['date'] = v
	        #cheque['date'] = str(datetime.strptime(v, '%Y%m%dT%H%M'))
            elif k == 's':
                cheque['sum'] = str(int(float(v)*100))
            elif k == 'fn':
                cheque['FN'] = v
            elif k == 'fp':
                cheque['FDP'] = v
            elif k == 'i':
                cheque['FD'] = v

        if len(cheque.keys()) != 5:
            return False

        return True

    @classmethod
    def qr_text_to_params(cls, text):
        if not cls.is_it_qr_text(text):
            return {}

        cheque = {}
        for e in text.split('&'):
            k, v = e.split('=')
            if k == 't':
                cheque['date'] = v
	        #cheque['date'] = str(datetime.strptime(v, '%Y%m%dT%H%M'))
            elif k == 's':
                cheque['sum'] = str(int(float(v)*100))
            elif k == 'fn':
                cheque['FN'] = v
            elif k == 'fp':
                cheque['FDP'] = v
            elif k == 'i':
                cheque['FD'] = v
        return cheque

    @classmethod
    def convert_data(cls, d):
        return d[0:4] + '-' + d[4:6] + '-' + d[6:11] + ':' + d[11:13] + ':' + d[13:15]

    @classmethod
    def qr_params_to_cheque_params(cls, qr_params):
        return {
            'fns_fiscalDocumentNumber': qr_params['FD'],
            'fns_fiscalDriveNumber': qr_params['FN'],
            'fns_fiscalSign': qr_params['FDP'],
            'fns_dateTime': cls.convert_data(qr_params['date']),
            'fns_totalSum': qr_params['sum'],
        }

    @classmethod
    def has_5_params_for_create_cheque(cls, s):
        p = cls.parse_1(s)
        for k in ['s', 'fn', 'fp', 'i', 't']:
            if not p.has_key(k):
                return False
        return True

    @classmethod
    def parse_1(cls, s1):
	t2 = s1.split(' ')
	p = {}
	for j in t2:
	    s = re.findall(u'^(\d+\.\d{1,2})$', j)
	    fn = re.findall(u'^(\d{16})$', j)
	    fp = re.findall(u'^(\d{9,10})$', j)
	    i = re.findall(u'^(\d{1,6})$', j)
	    time = re.findall(u'^(\d{1,2}\:\d{1,2}\:?\d{0,2})$', j)
	    date_1 = re.findall(u'^(\d{4}\.\d{1,2}\.\d{1,2})$', j)
	    date_2 = re.findall(u'^(\d{1,2}\.\d{1,2}\.\d{4})$', j)
	    date_time = re.findall(u'^(\d{8}T\d{1,2}\d{1,2}\d{0,2})$', j)
	    #'20201216T1818 29.00 9280440301295284 236 3107860384',

	    if s:
		p['s'] = re.findall(u'^(\d+\.\d{1,2})$', j)[0]
	    elif fn:
		p['fn'] = re.findall(u'^(\d{16})$', j)[0]
	    elif fp:
		p['fp'] = re.findall(u'^(\d{9,10})$', j)[0]
	    elif i:
		p['i'] = re.findall(u'^(\d{1,6})$', j)[0]
	    elif time:
		p['time'] = re.findall(u'^(\d{1,2}\:\d{1,2}\:?\d{1,2})$', j)[0]
	    elif date_1:
		p['date'] = re.findall(u'^(\d{4}\.\d{1,2}\.\d{1,2})$', j)[0]
	    elif date_2:
		p['date'] = re.findall(u'^(\d{1,2}\.\d{1,2}\.\d{4})$', j)[0]
		p['date'] = p['date'][6:10] + p['date'][3:5] + p['date'][0:2]
            elif date_time:
                p['date'] = re.findall(u'^(\d{8})T', j)[0]
                p['time'] = re.findall(u'T(\d{1,2}\d{1,2}\d{0,2})$', j)[0]
	    else:
		#print u'Alert not identify: %s' % j.encode('utf8')
		#print u'Alert not identify: %s' % j
		#print u'Alert not identify: ' + j
                pass

	    #if not p['s']:
	    #p['s'] = re.findall(u'^(\d+\.\d{1,2})$', i)

	#p['s'] = re.findall(u'(\d+\.\d{1,2})', s1)[0]
	#p['fn'] = re.findall(u'(\d{16})', s1)[0]
	#p['fp'] = re.findall(u'(\d{9,10})', s1)[0]
	#p['i'] = re.findall(u'(\d{1,6})', s1)[0]
	#p['time'] = re.findall(u'(\d{1,2}\:\d{1,2}\:?\d{1,2})', s1)[0]
	#p['date'] = re.findall(u'(\d{4}\.\d{1,2}\.\d{1,2})', s1)[0]

        if p.has_key('date') and p.has_key('time'):
    	    p['t'] = ''.join(p['date'].split('.')) + 'T' + ''.join(p['time'].split(':'))
    	    del p['time']
	    del p['date']
	
        return p

class ImportProverkachekaComFormatLikeFNS(object):
    """
    Класс отвечающий за импорт данных из ФНС России
    """

    @classmethod
    def get_fns_cheque_by_qr_params(cls, cheque, qr_text):
        #https://proverkacheka.com/check/get?fn=9288000100159749&fd=14492&fp=2104555358&n=1&s=293.90&t=05.12.2020+22%3A06&qr=0
        #url = 'https://proverkacheka.com/check/get?fn=' + cheque['FN'] + '&fd=' + cheque['FD'] + '&fp=' + cheque['FDP'] + '&n=1&s=' + cheque['sum'] + '&t=' + cheque['date'] + '&qr=0'
        #print url
	#webUrl = urllib.urlopen(url)
	#data = webUrl.read()
	#print "result code: " + str(webUrl.getcode()) 
	#print data

	req = urllib2.Request('https://proverkacheka.com/check/get')
        da = urllib.urlencode({
            #'qrraw': 't=20201107T2058&s=63.00&fn=9288000100192401&i=439&fp=2880362760&n=1',
            'qrraw': qr_text,
            'qr': 3,
        })
        data = urllib2.urlopen(url=req, data=da).read()
        #time.sleep(1)
        #print data

        # удалил блок html
        #data = '{"code":1,"data":{"json":{"code":3,"items":[{"nds":2,"sum":6300,"name":"Чизбургер с луком СБ","price":6300,"ndsSum":573,"quantity":1,"paymentType":4,"productType":1}],"nds10":573,"userInn":"7729532221","dateTime":"2020-11-07T20:58:00","kktRegId":"0000677159011474","operator":"Тамаева Минара","totalSum":6300,"creditSum":0,"fiscalSign":2880362760,"prepaidSum":0,"shiftNumber":6,"cashTotalSum":0,"provisionSum":0,"ecashTotalSum":6300,"operationType":1,"requestNumber":203,"fiscalDriveNumber":"9288000100192401","fiscalDocumentNumber":439,"fiscalDocumentFormatVer":2},"html":""}}'

        #return json.loads(data)
        fns_cheque_json = json.loads(data)

        #if not type(fns_cheque_json) is dict or \
        #    not fns_cheque_json.get('data') or \
        #    not type(fns_cheque_json['data']) is dict or \
        #    not fns_cheque_json['data'].get('json'):
        if not type(fns_cheque_json) is dict or not type(fns_cheque_json['data']) is dict:
            print u'Alert: This is not good JSON!'
            return

        fns_cheque_json["document"] = {}
        fns_cheque_json["document"]["receipt"] = fns_cheque_json['data']['json']

        return fns_cheque_json

class IsPackedAndWeight(object):
    """
    Для чеков на терриротии России
    по строке из  чека определяем является товар "весовым" - продаюзимся на вес или "упаковочны"
        и если он упаковочный пробуем вытащить из это сроки размер упаковки.
    """
    @classmethod
    def __create_words_from_cheque_title(cls, title):
        #title = title.replace('.',' ').replace('(',' ').replace(')',' ')

        #title = title.replace('.',' ') # Ащан для разделения слов, которые они сократили, использует точки. Просто так нельзя делать так как есть товар "Напиток б/а PEPSI жесть 0.33L"

        result = re.findall(u'(\d+\.\d+)', title)
        #print '========>>>>'
        #print 'title =', title.encode('utf8')
        #print 'len(result)=', len(result)
        #assert False
        #print 'result =', result
        if len(result) > 1:
            assert False
        elif len(result) == 1:
            result_update = result[0].replace('.',',')
            #print 'result_update =', result_update
            title = title.replace(result[0], ' ' + result_update)
            #print 'title =', title.encode('utf8')

        title = title.replace('.',' ')
        #print 'title =', title.encode('utf8')
        #print '<<========'

        words = []
        for word in title.split():
            #word = word.replace('.','').replace('(','').replace(')','')
            word = word.replace(',','.')
            word = word.upper()
            #if len(word) > 2:
            if len(word) > 1: # не проходит "2L" из "Напиток б/а PEPSI Light с/газ  2L"
                words.append(word)
        return words

    @classmethod
    def __get_weight_in_gram_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_gram(word)
        if result:
            weight = int(result[0])
            return weight
        else:
            assert False

    @classmethod
    def __get_weight_in_kilogram_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_kilogram(word)
        if result:
            weight = float(result[0])*1000
            return weight
        else:
            assert False

    @classmethod
    def __get_weight_in_litr_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_litr(word)
        if result:
            weight = float(result[0])*1000
            return weight
        else:
            assert False

    @classmethod
    def has_weight_from_cheque_title(cls, title):
        for word in cls.__create_words_from_cheque_title(title):
            if cls.__has_weight_in_gram_for_title(word) or \
                cls.__has_weight_in_kilogram_for_title(word) or \
                cls.__has_weight_in_litr_for_title(word):
                return True
        else:
            return False
        #OLD version
        try:
            w = cls.weight_from_cheque_title(title)
            return True
        except:
            import traceback
            traceback.print_exc()
            #traceback.print_exception()
            import sys
            print sys.exc_info()
            traceback.print_exception(*sys.exc_info())
            #traceback.print_stack()
            print '------------'

            return False

    @classmethod
    def __has_weight_in_gram_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_gram(word)
        if result:
            return True
        else:
            return False

    @classmethod
    def __has_weight_in_kilogram_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_kilogram(word)
        if result:
            return True
        else:
            return False

    @classmethod
    def __has_weight_in_litr_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_litr(word)
        if result:
            return True
        else:
            return False

    #@classmethod
    #def is_packed_from_cheque_title(cls, title):
    #    for word in cls.__create_words_from_cheque_title(title):
    #        if cls.__has_weight_in_gram_for_title(word):
    #            is_packed = True
    #            break
    #        elif cls.__has_weight_in_kilogram_for_title(word):
    #            is_packed = True
    #            break
    #        else:
    #            is_packed = False
    #    return is_packed

    @classmethod
    def __prepare_date_for_match_weight_in_gram(cls, word):
        result_g = re.findall(u'^(\d+)г$', word)
        result_gg = re.findall(u'^(\d+)Г$', word)
        result_gr = re.findall(u'^(\d+)гр$', word)
        result_grgr = re.findall(u'^(\d+)ГР$', word)
        return result_g + result_gg + result_gr + result_grgr

    @classmethod
    def __prepare_date_for_match_weight_in_kilogram(cls, word):
        #result_kg = re.findall(u'^(\d*.&\d+)кг$', word)
        result_kg = re.findall(u'^(\d*.?\d+)кг$', word)
        result_kgkg = re.findall(u'^(\d*.?\d+)КГ$', word)
        return result_kg + result_kgkg

    @classmethod
    def __prepare_date_for_match_weight_in_litr(cls, word):
        result_l = re.findall(u'^(\d*.?\d+)л$', word)
        result_ll = re.findall(u'^(\d*.?\d+)Л$', word)
        result_lll = re.findall(u'^(\d*.?\d+)L$', word)
        result_llll = re.findall(u'^(\d*.?\d+)l$', word)
        #print 'word =',word.encode('utf8')
        #print result_l + result_ll + result_lll + result_llll
        return result_l + result_ll + result_lll + result_llll

    @classmethod
    def weight_from_cheque_title(cls, title):
        for word in cls.__create_words_from_cheque_title(title):
            if cls.__has_weight_in_gram_for_title(word):
                weight = cls.__get_weight_in_gram_for_title(word)
                break
            elif cls.__has_weight_in_kilogram_for_title(word):
                weight = cls.__get_weight_in_kilogram_for_title(word)
                break
            elif cls.__has_weight_in_litr_for_title(word):
                weight = cls.__get_weight_in_litr_for_title(word)
                break
        else:
            assert False
            print 'Alert: not find weight!'
            return 0
        return float("{0:.3f}".format(float(weight)))
        #return float(weight)


