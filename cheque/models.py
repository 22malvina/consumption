# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from company.models import Company

import time
import json
import urllib
import urllib2, base64

import re

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

class FNSCheque(models.Model):
    json = models.TextField(blank=True, )
    company = models.ForeignKey(Company, blank=True, null=True) #TODO чек простой элемент и компанию надо вынести из чека
#    datetime_create = models.DateTimeField(blank=True, auto_now_add = True)
    fns_userInn = models.CharField(blank=True, max_length=254) # ИНН организации
    fns_fiscalDocumentNumber = models.CharField(blank=True, max_length=254)
    fns_fiscalDriveNumber = models.CharField(blank=True, max_length=254)
    fns_fiscalSign = models.CharField(blank=True, max_length=254)

    fns_dateTime = models.CharField(blank=True, max_length=254)
    fns_totalSum = models.CharField(blank=True, max_length=254)

    def format_date_qr_srt(self):
        #return str(self.fns_dateTime[0:4]) + str(self.fns_dateTime[5:7]) + str(self.fns_dateTime[8:10]) + 'T' + str(self.fns_dateTime[11:13]) + str(self.fns_dateTime[14:16]) 
        return str(self.fns_dateTime[8:10]) + str(self.fns_dateTime[5:7]) + str(self.fns_dateTime[0:4]) + 'T' + str(self.fns_dateTime[11:13]) + str(self.fns_dateTime[14:16]) 

    def format_sum_qr_srt(self):
        return str(self.fns_totalSum[0:-2]) + '.' + str(self.fns_totalSum[-2:])

    def get_datetime(self):
        return self.fns_dateTime

    @staticmethod
    def import_from_proverkacheka_com_format_like_fns(qr_text, company):
        cheque = QRCodeReader.qr_text_to_params(qr_text)
        #fns_cheque_info_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params(cheque)
        fns_cheque_info_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params(cheque, qr_text)

        #if not type(fns_cheque_info_json) is dict or \
        #    not fns_cheque_info_json.get('data') or \
        #    not type(fns_cheque_info_json['data']) is dict or \
        #    not fns_cheque_info_json['data'].get('json'):
        if not type(fns_cheque_info_json) is dict or not type(fns_cheque_info_json['data']) is dict:
            print u'Alert: This is not good JSON!'
            return

        fns_cheque_info_json["document"] = {}
        fns_cheque_info_json["document"]["receipt"] = fns_cheque_info_json['data']['json']

        account = None
        if FNSCheque.has_cheque_with_fiscal_params(company, account, 
            fns_cheque_info_json["document"]["receipt"]["fiscalDocumentNumber"],
            fns_cheque_info_json["document"]["receipt"]["fiscalDriveNumber"],
            fns_cheque_info_json["document"]["receipt"]["fiscalSign"],
            fns_cheque_info_json["document"]["receipt"]["dateTime"],
            fns_cheque_info_json["document"]["receipt"].get("totalSum", 'Error')):
            print u'Alert: We has this cheque!'
            #Такой чек уже существует'
            return
        FNSCheque.save_cheque_from_fns_cheque_json(company, fns_cheque_info_json)

    @classmethod
    def has_cheque_with_fiscal_params(cls, company, accaunt, fiscalDocumentNumber, fiscalDriveNumber, fiscalSign, dateTime, totalSum):
        for cheque in FNSCheque.objects.filter(
            company=company,
            fns_fiscalDocumentNumber=fiscalDocumentNumber,
            fns_fiscalDriveNumber=fiscalDriveNumber,
            fns_fiscalSign=fiscalSign,
            fns_dateTime=dateTime,
            fns_totalSum=totalSum):
            print '---has cheque----------'
            print cheque
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
        if cls.has_cheque_with_fiscal_params(company, account,
            fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"],
            fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"],
            fns_cheque_json["document"]["receipt"]["fiscalSign"],
            fns_cheque_json["document"]["receipt"]["dateTime"],
            fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')):
            print u'Alert: Find same cheque!'
            assert False

        # везде добавил временуж зону Москва timezone
        datetime_buy = fns_cheque_json["document"]["receipt"]["dateTime"] + '+03:00'

        fns_cheque = FNSCheque(
            company=company,
            json=fns_cheque_json,
            fns_userInn=fns_cheque_json["document"]["receipt"]["userInn"],
            fns_dateTime=datetime_buy
        )

        fns_cheque.fns_fiscalDocumentNumber = fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"]
        fns_cheque.fns_fiscalDriveNumber = fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"]
        fns_cheque.fns_fiscalSign = fns_cheque_json["document"]["receipt"]["fiscalSign"]
        fns_cheque.fns_dateTime = fns_cheque_json["document"]["receipt"]["dateTime"]
        fns_cheque.fns_totalSum = fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')

        fns_cheque.save()
        for elemnt in fns_cheque_json["document"]["receipt"].get("items", []):
            #Сначало можно попытаться найти найти товар с таким же названием и пустыми поялми чтобы лишний раз не делать одно и тоже
            fns_cheque_element = FNSChequeElement(
                fns_cheque=fns_cheque,
                quantity=elemnt.get("quantity", "Error"),
                name=elemnt.get("name", "Error"),
                price=elemnt.get("price", "Error"),
                sum=elemnt.get("sum", "Error"),
            )
            fns_cheque_element.save()

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

    def get_title(self):
        return self.name

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

    def get_weight(self):
        if self.__has_weight_from_title() and self.volume:
            if float(self.__get_weight_from_title()) == float(self.volume):
                return float(self.volume * self.quantity)
            else:
                print 'Error: Not rigth weight!'
                assert False
        elif self.__has_weight_from_title():
            return float(self.__get_weight_from_title() * self.quantity)
        elif self.volume:
            return float(self.volume * self.quantity)
        else:
            print 'Error: Not have weight!'
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
        return self.name.encode('utf8') + str(' ') + str(self.quantity) + str(' ') + str(self.volume)# + self.name.encode('utf8') 
 
class QRCodeReader(object):
    @classmethod
    def qr_text_to_params(cls, text):
        #qr_text = 't=20200523T2158&s=3070.52&fn=9289000100405801&i=69106&fp=3872222871&n=1'
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

        return json.loads(data)

class IsPackedAndWeight(object):
    """
    Для чеков на терриротии России
    по строке из  чека определяем является товар "весовым" - продаюзимся на вес или "упаковочны"
        и если он упаковочный пробуем вытащить из это сроки размер упаковки.
    """
    @classmethod
    def __create_words_from_cheque_title(cls, title):
        #title = title.replace('.',' ').replace('(',' ').replace(')',' ')
        title = title.replace('.',' ') # Ащан для разделения слов, которые они сократили, использует точки
        words = []
        for word in title.split():
            #word = word.replace('.','').replace('(','').replace(')','')
            word = word.replace(',','.')
            word = word.upper()
            if len(word) > 2:
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
    def has_weight_from_cheque_title(cls, title):
        try:
            w = cls.weight_from_cheque_title(title)
            return True
        except:
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
        result_kg = re.findall(u'^(\d*.&\d+)кг$', word)
        result_kgkg = re.findall(u'^(\d*.?\d+)КГ$', word)
        return result_kg + result_kgkg

    @classmethod
    def weight_from_cheque_title(cls, title):
        for word in cls.__create_words_from_cheque_title(title):
            if cls.__has_weight_in_gram_for_title(word):
                weight = cls.__get_weight_in_gram_for_title(word)
                break
            elif cls.__has_weight_in_kilogram_for_title(word):
                weight = cls.__get_weight_in_kilogram_for_title(word)
                break
        else:
            assert False
            print 'Alert: not find weight!'
            return 0
        return float("{0:.3f}".format(float(weight)))
        #return float(weight)


