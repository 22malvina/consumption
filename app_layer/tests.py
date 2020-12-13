# -*- coding: utf-8 -*-
from django.test import TestCase
from prediction.models import Element, Prediction, PredictionLinear, PredictionLinearFunction
from product_card.models import ProductCard
from offer.models import Offer, ChequeOffer
from company.models import Company, Employee
from cheque.models import FNSCheque, FNSChequeElement, QRCodeReader 
from datetime import datetime

#from prediction.tests.Base import list_buy_milk 
from prediction.tests import Base as BasePrediction 
#print Base.list_buy_milk()

import json
import time
import urllib
import urllib2, base64



from loader.cheque.proverkacheka_com import generate_cheque_qr_codes


class Base(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_1(self):
        """
        Польователь первый раз пользуется сейрвисом

        Создать пользователя по клиентским данным
        Создать пользовтаелю сомпанию
        """

	pety_employee = Employee(title='Pety', key='123zxc')
	pety_employee.save()

	company_family = Company(title='family')
	company_family.save()
	company_family.employees.add(pety_employee)
        company_family.title = 'test'
        self.assertEqual('test', company_family.title)

	company_family = Company.objects.get(employees__in=[pety_employee])
        self.assertEqual('family', company_family.title)

    def test_2(self):
        """
        пользователь хочет зашрузить инфо по чеку

        Должен авторизоваться
            получить сессию
        Отправить текс из QR кода
            для сохранения вбрана компания по мумолчанию
        Получить сохранненый чек из базы по параметрам 
        """

        #TODO пока проинициализируем так
        self.test_1()

        #in
        key = '123zxc'
        qr_text = 't=20201107T2058&s=63.00&fn=9288000100192401&i=439&fp=2880362760&n=1'
        self.assertEqual(0, FNSCheque.objects.all().count())

        #calc
        pety_employee = Employee.objects.get(key=key)
        self.assertEqual('Pety', pety_employee.title)

	company_family = Company.objects.get(employees__in=[pety_employee])

        FNSCheque.import_from_proverkacheka_com_format_like_fns(qr_text, company_family)
        self.assertEqual(1, FNSCheque.objects.all().count())

        cheque_p = QRCodeReader.qr_text_to_params(qr_text)
        cheque = FNSCheque.objects.get(fns_fiscalDocumentNumber=cheque_p['FD'], fns_fiscalDriveNumber=cheque_p['FN'], fns_fiscalSign=cheque_p['FDP'])
        cheque.company = Company.objects.get(employees__in=[pety_employee])
        cheque.save()

        FNSCheque.import_from_proverkacheka_com_format_like_fns(qr_text, company_family)
        FNSCheque.import_from_proverkacheka_com_format_like_fns('t=11&s=22&fn=33&i=44&fp=55&n=1', company_family)
        self.assertEqual(1, FNSCheque.objects.all().count())

    def test_3(self):
        """
        Петя хочет загрузить еще несколко чеков
            загрцзить все имеющиеся чеки
        выбтащить и посмотреть что ему скакжет авто сгереренаяя функйция потребления Молока.
        """
        pass

    def test_4(self):
        """
        импорт из https://proverkacheka.com/check&p=2

        получить все чеки
            получить последний чек загруденный Робо1
            загружать последоватетно страницы из https://proverkacheka.com/check&p=2 до тех пор пока не найдем на странице последний чек
                загрузить страницу
                вытащить из нее чеки
                    преобразовав чеки в формат для сравнения как текст из QR кода
                        параметров всего 5
                попыиаиься найти нужный чек
                если не нашли загрузить следубщую, ограничимся 100 страницами, но первый раз гораничение в 7000
        сохранить их в репозиторий от имени Робо1
             получить список QR кодов скормить его стандартном мехаизму сохранения чеков у пользователей
        потом возможно использовать их для показа похожих товаров в других магазинах и рекомедации цены
        """

	robo1_employee = Employee(title='robo1', key='robo1_123zxc')
	robo1_employee.save()

	company_family = Company(title='family')
	company_family.save()
	company_family.employees.add(robo1_employee)

        last_fns_cheques = FNSCheque.objects.filter(company=company_family).order_by('-id')
        has_last_fns_cheques = False
        if last_fns_cheques:
            has_last_fns_cheques = True
            last_fns_cheque = last_fns_cheques[0]

	cheque_params = generate_cheque_qr_codes(has_last_fns_cheques, last_fns_cheques)

        self.assertEqual(0, FNSCheque.objects.all().count())
        self.assertEqual(0, FNSChequeElement.objects.all().count())
	for s in cheque_params:
	    print s
	    #TODO нужно передовать компанию для которой сохряняются чеки
	    FNSCheque.import_from_proverkacheka_com_format_like_fns(s, company_family)
	#print 'sleep'
	#time.sleep(10)
        self.assertEqual(50, FNSCheque.objects.all().count())
        self.assertTrue(99 < FNSChequeElement.objects.all().count())


    def test_5(self):
        """
	зайти на ресурс и посмотреть офферы каких витирин воообще присутсвуют.
	1. товары можно искать тестовой строкой
	2. дерево категорий товаров
	"""
	
	company_family = Company(title='family')
	company_family.save()

	for i in BasePrediction.list_buy_milk():
	    fns_cheque = FNSCheque(company=company_family, fns_dateTime=i['dateTime'], json={'data': {'json': i}})
	    fns_cheque.save() 
	    for j in i['items']:
		e = FNSChequeElement(fns_cheque=fns_cheque, name=j['name'], quantity=j['quantity'], volume=j['volume'], sum=j['sum'], price=j['price'])
		e.save()

	for i in BasePrediction.list_buy_cheese():
	    fns_cheque = FNSCheque(company=company_family, fns_dateTime=i['dateTime'], json={'data': {'json': i}})
	    fns_cheque.save() 
	    for j in i['items']:
		e = FNSChequeElement(fns_cheque=fns_cheque, name=j['name'], quantity=j['quantity'], volume=j['volume'], sum=j['sum'], price=j['price'])
		e.save()

	#создавать офферы на основе имеющихся сущностей
	text = u'СЫР'
	offers = ChequeOffer.find(text)

	self.assertEqual([
	    {u'datetime': {u'update': u'2020-05-28T22:51:00'},
	    u'price': {u'one': 13500, u'per_one_gram': 61363.64},
	    u'product': {u'title': u'4607004891694 \u0421\u042b\u0420 \u0421\u041b\u0418\u0412\u041e\u0427\u041d\u042b\u0419 HOCHLA'},
	    u'showcase': {u'address': u'107076, \u0433.\u041c\u043e\u0441\u043a\u0432\u0430, \u0443\u043b.\u0411\u043e\u0433\u043e\u0440\u043e\u0434\u0441\u043a\u0438\u0439 \u0412\u0430\u043b, \u0434.6, \u043a\u043e\u0440\u043f.2'}},
	    {u'datetime': {u'update': u'2020-05-28T22:51:00'},
	    u'price': {u'one': 13990, u'per_one_gram': 55960.0},
	    u'product': {u'title': u'8600742011658 \u0421\u042b\u0420 \u0421\u0415\u0420\u0411\u0421\u041a\u0410\u042f \u0411\u0420\u042b\u041d\u0417\u0410'},
	    u'showcase': {u'address': u'107076, \u0433.\u041c\u043e\u0441\u043a\u0432\u0430, \u0443\u043b.\u0411\u043e\u0433\u043e\u0440\u043e\u0434\u0441\u043a\u0438\u0439 \u0412\u0430\u043b, \u0434.6, \u043a\u043e\u0440\u043f.2'}},
	    {u'datetime': {u'update': u'2020-05-15T20:45:00'},
	    u'price': {u'one': 49990, u'per_one_gram': 49990.0},
	    u'product': {u'title': u'2364939000004 \u0421\u042b\u0420 \u041a\u041e\u0420\u041e\u041b\u0415\u0412\u0421\u041a\u0418\u0419 51%'},
	    u'showcase': {u'address': u'\u0433.\u041c\u043e\u0441\u043a\u0432\u0430, \u0443\u043b.\u0411\u043e\u0433\u043e\u0440\u043e\u0434\u0441\u043a\u0438\u0439 \u0412\u0430\u043b, \u0434.6, \u043a\u043e\u0440\u043f.2'}},
	    {u'datetime': {u'update': u'2020-05-10T21:08:00'},
	    u'price': {u'one': 59990, u'per_one_gram': 59990.0},
	    u'product': {u'title': u'2316971000009 \u0421\u042b\u0420 \u041c\u0410\u0410\u0421\u0414\u0410\u041c 45% \u0418\u0427\u0410\u041b'},
	    u'showcase': {u'address': u'\u0433.\u041c\u043e\u0441\u043a\u0432\u0430, \u0443\u043b.\u0411\u043e\u0433\u043e\u0440\u043e\u0434\u0441\u043a\u0438\u0439 \u0412\u0430\u043b, \u0434.6, \u043a\u043e\u0440\u043f.2'}},
	    {u'datetime': {u'update': u'2020-04-21T14:04:00'},
	    u'price': {u'one': 50306, u'per_one_gram': 50306.0},
	    u'product': {u'title': u'2372240000002 \u0421\u042b\u0420 \u0413\u0420\u0410\u041d\u0414 SPAR 45%'},
	    u'showcase': {u'address': u'\u0433.\u041c\u043e\u0441\u043a\u0432\u0430, \u0443\u043b.\u0411\u043e\u0433\u043e\u0440\u043e\u0434\u0441\u043a\u0438\u0439 \u0412\u0430\u043b, \u0434.6, \u043a\u043e\u0440\u043f.2'}},
	    {u'datetime': {u'update': u'2020-04-21T14:04:00'},
	    u'price': {u'one': 37670, u'per_one_gram': 37670.0},
	    u'product': {u'title': u'2364178000001 \u0421\u042b\u0420  \u041c\u0410\u0410\u0421\u0414\u0410\u041c 45% \u041f\u0420\u0415'},
	    u'showcase': {u'address': u'\u0433.\u041c\u043e\u0441\u043a\u0432\u0430, \u0443\u043b.\u0411\u043e\u0433\u043e\u0440\u043e\u0434\u0441\u043a\u0438\u0439 \u0412\u0430\u043b, \u0434.6, \u043a\u043e\u0440\u043f.2'}},
	    {u'datetime': {u'update': u'2020-05-23T21:58:00'},
	    u'price': {u'one': 49900, u'per_one_gram': 49900.0},
	    u'product': {u'title': u'\u0421\u042b\u0420 \u0420\u041e\u0421\u0421\u0418\u0419\u0421\u041a\u0418\u0419 45%'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-05-23T21:58:00'},
	    u'price': {u'one': 18900, u'per_one_gram': 75600.0},
	    u'product': {u'title': u'\u0421\u042b\u0420 \u041c\u0410\u0421\u041a\u0410\u0420.80% 250\u0413\u0420'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-05-23T21:58:00'},
	    u'price': {u'one': 3399, u'per_one_gram': 37766.67},
	    u'product': {u'title': u'\u0421\u042b\u0420 \u041f\u041b \u0421 \u041b\u0423\u041a\u041e\u041c 90\u0413'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-05-23T21:58:00'},
	    u'price': {u'one': 3399, u'per_one_gram': 37766.67},
	    u'product': {u'title': u'\u0421\u042b\u0420 \u041f\u041b \u0412\u041e\u041b\u041d\u0410 45% 90\u0413'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-05-02T20:56:00'},
	    u'price': {u'one': 3899, u'per_one_gram': 48737.5},
	    u'product': {u'title': u'\u041f\u041b.\u0421\u042b\u0420 \u042f\u041d\u0422\u0410\u0420\u042c \u0424\u041e\u041b80\u0413'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-05-02T20:56:00'},
	    u'price': {u'one': 15900, u'per_one_gram': 39750.0},
	    u'product': {u'title': u'\u0421\u042b\u0420 \u041f\u041b \u0424\u0415\u0422\u0410\u041a\u0421\u0410 400\u0413'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-05-02T20:56:00'},
	    u'price': {u'one': 3399, u'per_one_gram': 37766.67},
	    u'product': {u'title': u'\u0421\u042b\u0420 \u041f\u041b \u0412\u041e\u041b\u041d\u0410 45% 90\u0413'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-05-02T20:56:00'},
	    u'price': {u'one': 3399, u'per_one_gram': 37766.67},
	    u'product': {u'title': u'\u0421\u042b\u0420 \u041f\u041b \u0412\u041e\u041b\u041d\u0410 45% 90\u0413'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-05-02T20:56:00'},
	    u'price': {u'one': 3899, u'per_one_gram': 48737.5},
	    u'product': {u'title': u'\u041f\u041b.\u0421\u042b\u0420 \u042f\u041d\u0422\u0410\u0420\u042c \u0424\u041e\u041b80\u0413'},
	    u'showcase': {u'address': u''}},
	    {u'datetime': {u'update': u'2020-06-03T14:50:00'},
	    u'price': {u'one': 59899, u'per_one_gram': 59899.0},
	    u'product': {u'title': u'2364178000001 \u0421\u042b\u0420  \u041c\u0410\u0410\u0421\u0414\u0410\u041c 45% \u041f\u0420\u0415'},
	    u'showcase': {u'address': u'107076, \u0433.\u041c\u043e\u0441\u043a\u0432\u0430, \u0443\u043b.\u0411\u043e\u0433\u043e\u0440\u043e\u0434\u0441\u043a\u0438\u0439 \u0412\u0430\u043b, \u0434.6, \u043a\u043e\u0440\u043f.2'}},
	    {u'datetime': {u'update': u'2020-06-03T14:50:00'},
	    u'price': {u'one': 20000, u'per_one_gram': 50000.0},
	    u'product': {u'title': u'4607004892677 \u0421\u042b\u0420 HOCHLAND \u041c\u042f\u0413\u041a\u0418\u0419'},
	    u'showcase': {u'address': u'107076, \u0433.\u041c\u043e\u0441\u043a\u0432\u0430, \u0443\u043b.\u0411\u043e\u0433\u043e\u0440\u043e\u0434\u0441\u043a\u0438\u0439 \u0412\u0430\u043b, \u0434.6, \u043a\u043e\u0440\u043f.2'}}
	], offers)

    def test_6(self):
        """
	получить последний по дате оффер, минимальный, и максимальный за последнюю неделю/месяц/квартал/год/все время , 201213 1212 для адреса
	"""

	company_family = Company(title='family')
	company_family.save()

	for i in BasePrediction.list_buy_milk():
	    fns_cheque = FNSCheque(company=company_family, fns_dateTime=i['dateTime'], json={'data': {'json': i}})
	    fns_cheque.save() 
	    for j in i['items']:
		e = FNSChequeElement(fns_cheque=fns_cheque, name=j['name'], quantity=j['quantity'], volume=j['volume'], sum=j['sum'], price=j['price'])
		e.save()

	for i in BasePrediction.list_buy_cheese():
	    fns_cheque = FNSCheque(company=company_family, fns_dateTime=i['dateTime'], json={'data': {'json': i}})
	    fns_cheque.save() 
	    for j in i['items']:
		e = FNSChequeElement(fns_cheque=fns_cheque, name=j['name'], quantity=j['quantity'], volume=j['volume'], sum=j['sum'], price=j['price'])
		e.save()

	#создавать офферы на основе имеющихся сущностей
	text = u'МОЛОКО'
	offers = ChequeOffer.find(text)

	print "==================================="

	#self.assertEqual([], offers)
	
	#2) как то их группируем - наверно в рамках одной витрины (инн + ритеил адресс), но даже если оффер меняется(изменилось название в чеке - это происходит очень редко и не важно, даже больше скажем что важно только последнее) т.е. если название в рамках одного магазина разные то это разные продукты
	

	#{u'datetime': {u'update': u'2020-06-03t14:50:00'},
	#u'price': {u'one': 20000, u'per_one_gram': 50000.0},
	#u'product': {u'title': u'4607004892677 \u0421\u042b\u0420 hochland \u041c\u042f\u0413\u041a\u0418\u0419'},
	#u'showcase': {u'address': '107076, \xd0\xb3.\xd0\x9c\xd0\xbe\xd1\x81\xd0\xba\xd0\xb2\xd0\xb0, \xd1\x83\xd0\xbb.\xd0\x91\xd0\xbe\xd0\xb3\xd0\xbe\xd1\x80\xd0\xbe\xd0\xb4\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9 \xd0\x92\xd0\xb0\xd0\xbb, \xd0\xb4.6, \xd0\xba\xd0\xbe\xd1\x80\xd0\xbf.2'}}

	split_by_offer_groups = []

	groups = {}
	for offer in offers:
	    #print offer['product']['title'].encode('utf8') 
	    #print offer['showcase']['address'].encode('utf8')
	    #print offer['showcase']['address']
	    #key = offer['product']['title'] + str(offer['showcase']['address'])
	    key = offer['product']['title'].encode('utf8') + ' ' + (offer['showcase']['address'].encode('utf8') if offer['showcase']['address'] else '')
	    #print type(offer['showcase']['address'])
	    #print type(offer['product']['title'])
	    #print type(offer['product']['title'].encode('utf8'))
	    #key = ''.join([offer['showcase']['address'], offer['product']['title']])
	    if not groups.get(key):
		groups[key] = []
	    groups[key].append(offer)

	for k in groups.keys():
	    split_by_offer_groups.append(groups[k])

	self.assertEqual([], split_by_offer_groups)
	


	    

#3) формируем для каждого 100% совпадения названия соответствующую матрицу из описания с разбивкой по диапазонам.
