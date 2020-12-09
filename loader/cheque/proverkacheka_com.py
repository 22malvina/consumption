# -*- coding: utf-8 -*-
from prediction.models import Element, Prediction, PredictionLinear, PredictionLinearFunction
from company.models import Company, Employee
from cheque.models import FNSCheque, FNSChequeElement, QRCodeReader 

from datetime import datetime
import json
import time
import urllib
import urllib2, base64

import re

MAX_LOAD_PAGE_COUNT = 7000
AVERAGE_LOAD_PAGE_COUNT = 100

#MAX_LOAD_PAGE_COUNT = 3
#AVERAGE_LOAD_PAGE_COUNT = 5

def generate_cheque_qr_codes(has_last_fns_cheques, last_fns_cheques):
        limit = AVERAGE_LOAD_PAGE_COUNT
        if not has_last_fns_cheques:
            limit = MAX_LOAD_PAGE_COUNT

	cheque_params = []
        for i in range(1, limit):
	    req = urllib2.Request('https://proverkacheka.com/check?p=' + str(i))
            #data = urllib.urlencode({
            #    #'qrraw': 't=20201107T2058&s=63.00&fn=9288000100192401&i=439&fp=2880362760&n=1',
            #    #'qr': 3,
            #})
            #data = urllib2.urlopen(url=req, data=data).read()
            data = urllib2.urlopen(url=req).read()
            #data = """
	    #  <div>
	    #    <a href="/check/9280440300607920-22793-294326115">чек на сумму 4348.00 руб. от 08.12.2020 23:07</a>
	    #  </div>
	    #    <a href="/check/9282000100456038-18702-3321673556">чек на сумму 3360.00 руб. от 12.11.2020 17:34</a>
	    #    <small>09.12.2020 23:30:37</small>
	    #    <a href="/check/8710000101035687-1842-3330187773">чек на сумму 5000.00 руб. от 26.09.2018 12:35</a>
            #"""
	    #data = """
	    #  <td>529781</td>
	    #  <td>09.12.2020 21:16:39</td>
	    #  <td>146.16</td>
	    #  <td>09.12.2020 17:18</td>
	    #  <td><a href="/check/9280440300918354-171007-1119865903" class="btn"><i class="fas fa-info-circle"></i></a></td>
	    #"""
            #print data

            #<a href="/check/9282000100456038-18702-3321673556">чек на сумму 3360.00 руб. от 12.11.2020 17:34</a>
            #result = re.findall(r'/check/(\d+)-(\d+)-(\d+).*?сумму (\d+)\.(\d+) руб. от (\d+)\.(\d+)\.(\d+) (\d+):(\d+) \<',data)
            #result = re.findall(r'/check/(\d+)-(\d+)-(\d+).*? (\d+)\.(\d+) .*? (\d+)\.(\d+)\.(\d+) (\d+):(\d+)',data)

            r1 = re.findall(r'<td><a href="/check/(\d+)-(\d+)-(\d+)',data)
            r2 = re.findall(r'\<td\>(\d+)\.(\d+)\.(\d+) (\d+):(\d+)\<\/td\>',data)
            r3 = re.findall(r'\<td\>(\d+\.\d+)\<\/td\>',data)
	    if not len(r1) == len(r2) == len(r3):
		print len(r1), len(r2), len(r3)
		assert False
	    for j in range(0, len(r1)):
		#qr_text = 't=20200523T2158&s=3070.52&fn=9289000100405801&i=69106&fp=3872222871&n=1'
		cheque_params.append('t=' + r2[j][0] + r2[j][1] + r2[j][2] + 'T' + r2[j][3] + r2[j][4] + '&s=' + r3[j] + '&fn=' + r1[j][0] + '&i=' + r1[j][1] + '&fp=' + r1[j][2] + '&n=1')

	return cheque_params


