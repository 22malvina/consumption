# -*- coding: utf-8 -*-
from django.test import TestCase
from prediction.models import Element, Prediction, PredictionLinear, PredictionLinearFunction
from product_card.models import ProductCard
from offer.models import Offer
from company.models import Company, Employee
from cheque.models import FNSCheque, FNSChequeElement, QRCodeReader 
from datetime import datetime

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
        FNSCheque.import_from_proverkacheka_com_format_like_fns(qr_text)
        self.assertEqual(1, FNSCheque.objects.all().count())

        cheque_p = QRCodeReader.qr_text_to_params(qr_text)
        cheque = FNSCheque.objects.get(fns_fiscalDocumentNumber=cheque_p['FD'], fns_fiscalDriveNumber=cheque_p['FN'], fns_fiscalSign=cheque_p['FDP'])
        cheque.company = Company.objects.get(employees__in=[pety_employee])
        cheque.save()

        FNSCheque.import_from_proverkacheka_com_format_like_fns(qr_text)
        FNSCheque.import_from_proverkacheka_com_format_like_fns('t=11&s=22&fn=33&i=44&fp=55&n=1')
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

#        limit = 5
#        if not has_last_fns_cheques:
#            limit = 3
#
#        import re
#	cheque_params = []
#        for i in range(1, limit):
#	    req = urllib2.Request('https://proverkacheka.com/check?p=' + str(i))
#            #data = urllib.urlencode({
#            #    #'qrraw': 't=20201107T2058&s=63.00&fn=9288000100192401&i=439&fp=2880362760&n=1',
#            #    #'qr': 3,
#            #})
#            #data = urllib2.urlopen(url=req, data=data).read()
#            data = urllib2.urlopen(url=req).read()
#            #data = """
#	    #  <div>
#	    #    <a href="/check/9280440300607920-22793-294326115">чек на сумму 4348.00 руб. от 08.12.2020 23:07</a>
#	    #  </div>
#	    #    <a href="/check/9282000100456038-18702-3321673556">чек на сумму 3360.00 руб. от 12.11.2020 17:34</a>
#	    #    <small>09.12.2020 23:30:37</small>
#	    #    <a href="/check/8710000101035687-1842-3330187773">чек на сумму 5000.00 руб. от 26.09.2018 12:35</a>
#            #"""
#	    #data = """
#	    #  <td>529781</td>
#	    #  <td>09.12.2020 21:16:39</td>
#	    #  <td>146.16</td>
#	    #  <td>09.12.2020 17:18</td>
#	    #  <td><a href="/check/9280440300918354-171007-1119865903" class="btn"><i class="fas fa-info-circle"></i></a></td>
#	    #"""
#            #print data
#            print i
#
#            #<a href="/check/9282000100456038-18702-3321673556">чек на сумму 3360.00 руб. от 12.11.2020 17:34</a>
#            #result = re.findall(r'/check/(\d+)-(\d+)-(\d+).*?сумму (\d+)\.(\d+) руб. от (\d+)\.(\d+)\.(\d+) (\d+):(\d+) \<',data)
#            #result = re.findall(r'/check/(\d+)-(\d+)-(\d+).*? (\d+)\.(\d+) .*? (\d+)\.(\d+)\.(\d+) (\d+):(\d+)',data)
#
#            r1 = re.findall(r'<td><a href="/check/(\d+)-(\d+)-(\d+)',data)
#            r2 = re.findall(r'\<td\>(\d+)\.(\d+)\.(\d+) (\d+):(\d+)\<\/td\>',data)
#            r3 = re.findall(r'\<td\>(\d+\.\d+)\<\/td\>',data)
#	    if not len(r1) == len(r2) == len(r3):
#		print len(r1), len(r2), len(r3)
#		assert False
#            #print result
#            #print 'len result =', len(result)
#	    for j in range(0, len(r1)):
#		#qr_text = 't=20200523T2158&s=3070.52&fn=9289000100405801&i=69106&fp=3872222871&n=1'
#		cheque_params.append('t=' + r2[j][0] + r2[j][1] + r2[j][2] + 'T' + r2[j][3] + r2[j][4] + '&s=' + r3[j] + '&fn=' + r1[j][0] + '&i=' + r1[j][1] + '&fp=' + r1[j][2] + '&n=1')
#
#	#print cheque_params

	cheque_params = generate_cheque_qr_codes(has_last_fns_cheques, last_fns_cheques)

        self.assertEqual(0, FNSCheque.objects.all().count())
        self.assertEqual(0, FNSChequeElement.objects.all().count())
	for s in cheque_params:
	    print s
	    FNSCheque.import_from_proverkacheka_com_format_like_fns(s)
	#print 'sleep'
	#time.sleep(10)
        self.assertEqual(50, FNSCheque.objects.all().count())
        self.assertTrue(99 < FNSChequeElement.objects.all().count())


