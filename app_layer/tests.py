# -*- coding: utf-8 -*-
from django.test import TestCase
from prediction.models import Element, Prediction, PredictionLinear, PredictionLinearFunction
from product_card.models import ProductCard
from offer.models import Offer
from company.models import Company, Employee
from cheque.models import ChequeFNS, ChequeFNSElement, QRCodeReader 
from datetime import datetime

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
        self.assertEqual(0, ChequeFNS.objects.all().count())

        #calc
        pety_employee = Employee.objects.get(key=key)
        self.assertEqual('Pety', pety_employee.title)
        ChequeFNS.import_from_proverkacheka_com_format_like_fns(qr_text)
        self.assertEqual(1, ChequeFNS.objects.all().count())

        cheque_p = QRCodeReader.qr_text_to_params(qr_text)
        cheque = ChequeFNS.objects.get(fns_fiscalDocumentNumber=cheque_p['FD'], fns_fiscalDriveNumber=cheque_p['FN'], fns_fiscalSign=cheque_p['FDP'])
        cheque.company = Company.objects.get(employees__in=[pety_employee])
        cheque.save()

        ChequeFNS.import_from_proverkacheka_com_format_like_fns(qr_text)
        ChequeFNS.import_from_proverkacheka_com_format_like_fns('t=11&s=22&fn=33&i=44&fp=55&n=1')
        self.assertEqual(1, ChequeFNS.objects.all().count())

    def test_3(self):
        """
        """
        pass

