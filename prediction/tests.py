# -*- coding: utf-8 -*-
from django.test import TestCase
from models import Element, Prediction, PredictionLinear
from product_card.models import ProductCard
from offer.models import Offer

class Base(TestCase):
    def setUp(self):
        self.maxDiff = None

	p = ProductCard(title="МОЛОКО ДВД 3.2%")
	p.save()
	p = ProductCard(title="МОЛОКО SPAR 3.2% 1.7 л.")
	p.save()
	p = ProductCard(title="МОЛОКО Простоквашино 3.2%")
	p.save()
	p = ProductCard(title="Творог SPAR 9%")
	p.save()


    def __list_buy_milk(self):
	return [
	    {
		"fiscalDocumentNumber":148436,
		"taxationType":1,
		"nds10":13873,
		"shiftNumber":386,
		"kktRegId":"0001734115017264",
		"operationType":1,
		"ecashTotalSum":207870,
		"requestNumber":182,
		"retailPlaceAddress":"г.Москва, ул.Богородский Вал, д.6, корп.2",
		"receiptCode":3,
		"fiscalSign":2166849586,
		"operator":"Усикова Дарья Игорев",
		"userInn":"5258056945",
		"user":"ООО \"Спар Миддл Волга\"",
		"fiscalDriveNumber":"9285000100127782",
		"cashTotalSum":0,
		"nds18":9212,
		"totalSum":207870,

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
		"retailPlaceAddress":"г.Москва, ул.Богородский Вал, д.6, корп.2",
	    },
	    {
		"dateTime":"2020-05-24T12:56:00",
		'items': [
		    {"weight": 1000, "quantity":1,"name":u"4607045982788 МОЛОКО SPAR УЛЬТРАПА","price":4990,"sum":4990, 'volume': 1},
		],
		"retailPlaceAddress":"г.Москва, ул.Богородский Вал, д.6, корп.2",
	    },
	    {
		"dateTime":"2020-05-23T21:58:00",
		'items': [
		    {"weight": 1400, "calculationTypeSign":4,"ndsRate":2,"name":u"МОЛОКО ПАСТ.3,7%1400","quantity":1,"ndsSum":726,"calculationSubjectSign":1,"sum":7990,"price":7990, 'volume': 1.4},
		],
		"retailPlaceAddress":"г.Москва, ул.Богородский Вал, д.6, корп.2",
	    },
	    {
		"dateTime":"2020-05-15T20:45:00",
		'items': [
		    {"weight": 925, "quantity":1,"name":u"4607167840416 МОЛОКО SPAR 3,2% 925","price":5490,"sum":5490, 'volume': 0.925},
		],
		"retailPlaceAddress":"г.Москва, ул.Богородский Вал, д.6, корп.2",
	    },
	    {
		"dateTime":"2020-05-10T21:08:00",
		'items': [
		    {"weight": 1700, "sum":8990,"price":8990,"quantity":1,"name":u"4607167841154 МОЛОКО SPAR 2,5% 1,7", 'volume': 1.7},
		],
		"retailPlaceAddress":"г.Москва, ул.Богородский Вал, д.6, корп.2",
	    },
	    {
		"dateTime":"2020-05-06T21:53:00",
		'items': [
		    {"quantity":1,"name":u"4607167841154 МОЛОКО SPAR 2,5% 1,7","price":8990,"sum":8990, 'volume': 1.7},
		    {"weight": 950,"quantity":1,"name":u"4690228007842 МОЛОКО ДОМИК В ДЕРЕВ","price":5990,"sum":5990, 'volume': 1},
		],
		"retailPlaceAddress":"г.Москва, ул.Богородский Вал, д.6, корп.2",
	    },
	    {
		"dateTime":"2020-03-28T19:58:00",
		'items': [
		    {"sum":4990,"price":4990,"name":u"4607167840416 МОЛОКО SPAR 3,2% 925","quantity":1, 'volume': 0.925},
		],
		"retailPlaceAddress":"Ашан",
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
		elements.append(Element(j['name'], i['dateTime'], j['volume']*j['quantity']))
	
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

	Как лучше сделать?
	    1) привязть определенный ресурс
		тогда придется по ресурсу определять
		    1.1) продкуты с которыми он связан или к которые подходит.
	    2) привязать карточку продукта
		тогда все ресурсы привязнные к карточе добавятся атоматом - НЕТ	 
		но легко будет искать то чем функцию расширить, т.е. аналоги - ДА

	Нужна ли функции явная связь с карточками продуктов?
	+
	1) упрощает поиск продуктов для замещения
	-
	1) пользователю придется привязывать все альтернативные продукты
	"""
	

	# получаю список ресурсов функции 
	list_buy_milk = self.__list_buy_milk()
	elements = []
	for i in list_buy_milk:
	    for j in i['items']:
		elements.append(Element(j['name'], i['dateTime'], j['volume']*j['quantity']))
	prediction = PredictionLinear(elements)
	
	product_cards = prediction.product_cards()

	#self.assertEqual([ProductCard(), ProductCard(), ProductCard()], product_cards)
	self.assertEqual(set([ProductCard.objects.get(id=1), ProductCard.objects.get(id=2), ProductCard.objects.get(id=3)]), product_cards)


    def test_3(self):
	"""
	показать пользователю все имеющиеся предложения на основе полученных карточек продуктов 
	"""

	product_cards = ProductCard.objects.all()
	
	offers = Offer.objects.filter(product_card__in=product_cards)
	self.assertEqual([], list(offers))

    def test_4(self):
	"""
	Создать офферы на основе 
	    1 чеков - человек
		найти по строке из чека, стоимости, магазину - подходящие продукты
		выбрать продукты для клоторых обновится оффер, так как это разовое событие то оно не может меняться а только меняться с временем
		    карточек продуктов может быть найдно много(так как пользователи могут создавать разные карточки)
			Обойти это можно создав супер карточку которую пользователи немогут менять но ккоторой могут привязывать свою
			    и эти супер карточки будут в отдельном дереве
			обновлять оыыер у 3 из 1000 карточек которые выбрал польователь.
	    2 ресурсов - человек
		найти на основе ресурса - подходящие продукты
		    что бы сделать оффер нужна цена, а у ресурса ее нет, так что не походит
		    но возможно стоит ввести отдельную сущность приоретения где фиксируются ресурсы и стоимости их приобретения.
	    3 ресурса основанного на чеке
		найти на основе ресурса и связанного с ним чека - продукты
	    4 импорта с сайтов - робот
		кадый робот знает как карточка продукта связана с элементом витрины к которой он подключен, для получения оффера
		    елемент витрины для сайта это может быть страница товара
			а иакже есть другме роботы которые обновляют информацию по карточек если на витрине она меняется - полу ручной режим
	"""

	#1
	#ChequeElement.objects.filter(
	list_buy_milk = self.__list_buy_milk()
	elements = []
	for i in list_buy_milk:
	    for j in i['items']:
		elements.append({'title': j['name'], 'price': j['price'], 'datetime_buy': i['dateTime']})

	#TODO тут идет ручной выбор карточек к которым надо создать оффер
	for e in elements:
	    for product_card in ProductCard.find_by_text(e['title']):
		offer = Offer(product_card=product_card, price=e['price'], datetime=e['datetime_buy'])
		offer.save()

	#for o in Offer.objects.all():
	#    print o

	product_cards = ProductCard.objects.all()
	
	offers = Offer.objects.filter(product_card__in=product_cards)
	#TODO результат наверно не верный так как продуктов похожих может быть больше
	self.assertEqual(27, len(offers))


    def test_5(self):
	"""
	показать пользователю все имеющиеся предложения на основе полученных карточек продуктов 
	"""
	product_cards = ProductCard.objects.all()
	
	offers = Offer.objects.filter(product_card__in=product_cards)
	self.assertEqual([], list(offers))



