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


