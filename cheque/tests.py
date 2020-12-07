# -*- coding: utf-8 -*-
from django.test import TestCase
from prediction.models import Element, Prediction, PredictionLinear, PredictionLinearFunction
from product_card.models import ProductCard
from offer.models import Offer
from company.models import Company, Employee
from cheque.models import ChequeFNS, ChequeFNSElement 
from datetime import datetime

class Base(TestCase):
    def setUp(self):
        self.maxDiff = None

    def test_1(self):
        #qr_text = 't=20201205T2206&s=293.90&fn=9288000100159749&i=14492&fp=2104555358&n=1'
        qr_text = 't=20201121T204000&s=390.96&fn=9285000100186911&i=123274&fp=1022052943&n=1'
        qr_text = 't=20201020T151800&s=96.00&fn=9287440300038062&i=44302&fp=1049436108&n=1'
        qr_text = 't=20201107T2058&s=63.00&fn=9288000100192401&i=439&fp=2880362760&n=1'
        ChequeFNS.import_from_proverkacheka_com_format_like_fns(qr_text)
        #ChequeFNS.import_from_fns(qr_text)

        for i in ChequeFNS.objects.all():
            print i
        for i in ChequeFNSElement.objects.all():
            print i

