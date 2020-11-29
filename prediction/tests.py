# -*- coding: utf-8 -*-
from django.test import TestCase
from models import Element, Prediction, PredictionLinear

class Base(TestCase):
    def setUp(self):
        self.maxDiff = None

    def __list_buy_milk(self):
	return [
	    {
		"dateTime":"2020-06-03T14:50:00",
		'items': [
		    {"price":5990,"name":u"4607045982771 МОЛОКО SPAR УЛЬТРАПА","quantity":3,"sum":17970, 'volume': 1},
		],
	    },
	    {
		"dateTime":"2020-05-28T22:51:00",
		'items': [
		    {"weight": 1000, "quantity":2,"sum":11980,"price":5990,"name":u"4607045982771 МОЛОКО SPAR УЛЬТРАПА", 'volume': 1},
		],
	    },
	    {
		"dateTime":"2020-05-24T12:56:00",
		'items': [
		    {"weight": 1000, "quantity":1,"name":u"4607045982788 МОЛОКО SPAR УЛЬТРАПА","price":4990,"sum":4990, 'volume': 1},
		],
	    },
	    {
		"dateTime":"2020-05-23T21:58:00",
		'items': [
		    {"weight": 1400, "calculationTypeSign":4,"ndsRate":2,"name":u"МОЛОКО ПАСТ.3,7%1400","quantity":1,"ndsSum":726,"calculationSubjectSign":1,"sum":7990,"price":7990, 'volume': 1.4},
		],
	    },
	    {
		"dateTime":"2020-05-15T20:45:00",
		'items': [
		    {"weight": 925, "quantity":1,"name":u"4607167840416 МОЛОКО SPAR 3,2% 925","price":5490,"sum":5490, 'volume': 0.925},
		],
	    },
	    {
		"dateTime":"2020-05-10T21:08:00",
		'items': [
		    {"weight": 1700, "sum":8990,"price":8990,"quantity":1,"name":u"4607167841154 МОЛОКО SPAR 2,5% 1,7", 'volume': 1.7},
		],
	    },
	    {
		"dateTime":"2020-05-06T21:53:00",
		'items': [
		    {"quantity":1,"name":u"4607167841154 МОЛОКО SPAR 2,5% 1,7","price":8990,"sum":8990, 'volume': 1.7},
		    {"weight": 950,"quantity":1,"name":u"4690228007842 МОЛОКО ДОМИК В ДЕРЕВ","price":5990,"sum":5990, 'volume': 1},
		],
	    },
	    {
		"dateTime":"2020-03-28T19:58:00",
		'items': [
		    {"sum":4990,"price":4990,"name":u"4607167840416 МОЛОКО SPAR 3,2% 925","quantity":1, 'volume': 0.925},
		],
	    },
	]


    def test_linear_forecasting_for_the_whole_period(self):
        """
        Попробуем линейное прогнозированите на всем периоде

        Идет потребление некоторых ресурсов постоянно но не очень системно.
        К примеру молоко.
        Покупается несколько раз внеделю.
        Изменять потребление не планируется.
        Попробуем линейно апроксимировать данную функцию.
	добавил нужгыеразмеры в нашем случае молоко употребляется в литрахт 'volume': 1

	сначала получим среднее потребление молока в день.
	    просумируем все потребление и поделимгачисло дней закоторое было произведено потребление
		получили в итоге производную

	далее попробуем полчить производную исключив один элемет потребления и сокративчисло дней до момента его приобретения

	затем рассчитам на сколько днейхватит послежней покупк если потребление будет таким же
	    сейчас рассматриваем простую можель когда потребление рассчитываеися от даты первой покупки до даты последней покупки.

	прибавим к дельте котороая между первой и последней покупкой, количество дней накоторых хватит последей покупки и получим дату когда нужно установить хакупку в календаре.
        """

	delta_days = 40
	delta_days_2 = 35

	list_buy_milk = self.__list_buy_milk()

	elements = []
	for i in list_buy_milk:
	    for j in i['items']:
		elements.append(Element(i['dateTime'], j['volume']*j['quantity']))
	
	#self.assertEqual('', elements)

	self.assertEqual(0.34, Prediction.average_weight_per_day_in_during_period(elements, delta_days))

	pl = PredictionLinear(elements)
	self.assertEqual(0.34, pl.average_weight_per_day_in_during_period(delta_days))

	#self.assertEqual(0.3, Prediction.average_weight_per_day_in_during_period(elements[1:], delta_days_2))
	delta = Prediction.average_weight_per_day_in_during_period(elements[1:], delta_days_2)
	self.assertEqual(0.3, delta)

	pl_2 = PredictionLinear(elements[1:])
	delta = pl_2.average_weight_per_day_in_during_period(delta_days_2)
	self.assertEqual(0.3, delta)

	#self.assertEqual(10.0, elements[0].get_weight() / delta) 
	days_continue_for_last_buy = elements[0].get_weight() / delta
	self.assertEqual(10.0, days_continue_for_last_buy)

	delta_days_future = pl.days_future(delta_days_2)
	self.assertEqual(10.0, delta_days_future)

	today_is = 45.0 #какойто день месяца в который долженсработать напоминание что сегоднявсе кончится.
	self.assertEqual(today_is, delta_days_2 + days_continue_for_last_buy)


    def test_2(self):
	"""
	Найти какрточки продуктов которые подойдут для данной функии потребления.

	Функция потребления состоит из:
	    1) ресурсы которые в нее включены
		а также продукты на которые ссылаются включенные ресурсы
	    2) учитывает все ресурсов которые обработаны в рамках данной фирм и не включенных в эту функцию.
		после обработки(добавления в другую ф. слеует подождать несколько дней так возможно еще не успели оработать)
		    простой случайесли ресурс добавлен в другую ф. в эту его автоматом не предлагать
	    3) ресурсов предложенных но отвергнутых пользователем
	    4) продуктов предложенных но отвергнутых пользоватеоем
	    5) есть авто функции которые есть у всех пользоватеей МОЛОКО 3.2% в них автоматом для рекомедаций добавлять все продукты и ресурсы с таким покащатеоем.
	"""

	# получаю список ресурсов функции 
	list_buy_milk = self.__list_buy_milk()
	elements = []
	for i in list_buy_milk:
	    for j in i['items']:
		elements.append(Element(i['dateTime'], j['volume']*j['quantity']))

	prediction = PredictionLinear(elements)
	
	product_cards = prediction.product_cards()
	self.assertEqual(0, 1)



