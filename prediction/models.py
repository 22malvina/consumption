# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from product_card.models import ProductCard
from cheque.models import FNSChequeElement
from datetime import datetime


class PredictionLinearFunction(models.Model):
    title = models.CharField(blank=True, max_length=254)
    cheque_elements = models.ManyToManyField(FNSChequeElement)
    #product_card = models.ForeignKey(ProductCard)
    datetime_create = models.DateTimeField(blank=True, auto_now_add = True)
    base_type = models.CharField(blank=True, max_length=254)

    def allow_key_words(self):
	key_words = set()
	if self.title:
	    key_words.add(self.title)
	    key_words.update(self.__utils_generate_key_words_from_title())
	if self.base_type:
	    key_words.add(self.base_type)
	    key_words.update(self.__utils_generate_key_words_from_base_type())
	return key_words
	#return [self.title]

    def cheque_have_name_like_name_from_contains_cheques(self):
	#найдем чеки с 100% совпадением названия и связанных чеков, и на основе них рассчитам предложение за килограм
	elements = set()
	for e in self.cheque_elements.all():
	    for en in FNSChequeElement.objects.filter(name=e.name):
		elements.add(en)
	return elements

    def cheque_contains_key_words(self):
	#взять ключевые слова у функции которые могут содержаться в чеках
	elements = set()
	for word in self.allow_key_words():
	    #print 'word =', word.encode('utf8')
	    qs = FNSChequeElement.objects.filter(name__icontains=word)
	    #qs = FNSChequeElement.objects.all()
	    for e_word in self.disallow_key_words():
		#print 'e_word =', e_word.encode('utf8')
		qs = qs.exclude(name__icontains=e_word)
	    #print qs.query
	    #print str(qs.query.decode('utf-8'))
	    for e in qs:
		elements.add(e)
	return elements

    def disallow_key_words(self):
	words = set()
	if self.base_type == u'СЫР':
	    for w in [u'СЫРОК', u'сырный', u'сыром']:
		words.update(self.__utils_generate_differnent_case(w))
	if self.base_type == u'МОЛОКО':
	    for w in [u'МОЛОЧНЫЙ']:
		words.update(self.__utils_generate_differnent_case(w))
		#words.update(self.__utils_generate_differnent_case('milk'))
	return words

    def elements(self):
	elements = []
	for i in self.cheque_elements.all():
	    e = i.consumption_element_params()
	    elements.append(Element(e['title'], e['datetime'], e['weight']))
	return elements

#    def __str__(self):
#        return u"%s (%s)" % (str(self.title), str(len(self.cheque_elements.all()))) 
#    #    #return u"%s %s (%s)" % (str(self.base_type), str(self.title), str(len(self.cheque_elements.all()))) 
#    #    return self.base_type # + u"%s (%s)" % (str(self.title), str(len(self.cheque_elements.all()))) 

    def __unicode__(self):
        return u"%s -> %s (%s)" % (self.base_type, self.title,  str(len(self.cheque_elements.all())) )

    def __utils_generate_key_words_from_title(self):
	#words = set()
	#words.add(self.title.lower())
	#words.add(self.title.upper())
	#words.add(self.title.capitalize())
	#return words
	return self.__utils_generate_differnent_case(self.title)

    def __utils_generate_key_words_from_base_type(self):
	#words = set()
	#words.add(self.base_type.lower())
	#words.add(self.base_type.upper())
	#words.add(self.base_type.capitalize())
	#return words
	return self.__utils_generate_differnent_case(self.base_type)

    def __utils_generate_differnent_case(self, word):
	words = set()
	words.add(word.lower())
	words.add(word.upper())
	words.add(word.capitalize())
	return words

class Element(object):
    def get_weight(self):
        return self.__weight
        #return self.__weight if self.__weight else self.__voluem

    def get_date(self):
        return self.__date

    def get_title(self):
	return self.__title

    def __init__(self, title, date, weight):
	self.__title = title
        self.__date = date
	self.__date = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
        self.__weight = weight

    def __unicode__(self):
        return u"%s -> %s" % (self.__date, self.__weight)

#class Prediction(models.Model): 
class Prediction(object): 
    """
    Каласс для рассчета потребелния
    """
    print 'Depricated'

    @classmethod
    #def average_weight_per_day_in_cluster_products_during_period_v1(cls, elements, delta_days):
    def average_weight_per_day_in_during_period(cls, resources, delta_days):
	all_weight = sum(map(lambda x: float(x.get_weight()), resources))
	return float("{0:.3f}".format(float(all_weight) / delta_days))

class PredictionLinear(object):
    """
    Класс рассчета линейного потребления

	ресурсы идут в порядке от от послежнего к самому раннему
    """
    def append(self, e):
	self.__resources.append(e)
	self.__resources = sorted(self.__resources, key = lambda x : x.get_date())

    @classmethod
    def auto_add_cheque_elements_to_functions(cls, fns_cheques):
	#TODO метод скрытыс образом выбирает функцию к котоорй привязывать, очень плохо
	#наполняем функции чеками которые им подходят
	for fns_cheque in fns_cheques:
	    #for fns_cheque_element in fns_cheque.elements():
	    for fns_cheque_element in FNSChequeElement.objects.filter(fns_cheque=fns_cheque):
		print '--->'
		print fns_cheque_element.get_title().encode('utf8')
		for base_function_type in PredictionLinear.base_function_types(fns_cheque_element):
		    function = PredictionLinearFunction.objects.get(base_type=base_function_type)
		    function.cheque_elements.add(fns_cheque_element)

    @classmethod
    def auto_find_available_base_function_type(cls, fns_cheques):
	#получем все типы базвых функий которые возможны
	base_function_types = set()
	for fns_cheque in fns_cheques:
	    #for fns_cheque_element in fns_cheque.elements():
	    for fns_cheque_element in FNSChequeElement.objects.filter(fns_cheque=fns_cheque):
		for base_function_type in PredictionLinear.base_function_types(fns_cheque_element):
		    base_function_types.add(base_function_type)
	for base_function_type in base_function_types:
	   print base_function_type.encode('utf8')
	print 
	return base_function_types

    def average_weight_per_day_from_first_buy_to_this_date(self, date_calc):
	delta_days = date_calc - self.__first_date()
	#all_weight = sum(map(lambda x: float(x.get_weight()), self.__resources))
	all_weight = 0
	for i in self.__resources:
	    if i.get_date().date() <= date_calc.date():
		all_weight += i.get_weight()

	if delta_days.days == 0:
	    print 'Error !!!'

	return float("{0:.3f}".format(float(all_weight) / delta_days.days))

    def average_weight_per_day_in_during_period(self):
	#delta_days = self.__last_date() - self.__first_date()
	#delta_days = delta_days.days
	delta_days = self.delta_days()
	all_weight = sum(map(lambda x: float(x.get_weight()), self.__resources))
	return float("{0:.3f}".format(float(all_weight) / delta_days))

    def __average_weight_per_day_in_during_period_without_last(self):
	delta_days = self.without_last_delta_days()
	#all_weight = sum(map(lambda x: float(x.get_weight()), self.__resources[1:]))
	#all_weight = sum(map(lambda x: float(x.get_weight()), self.__resources[:-1])) # возможно в одином чеке два разных пакета полока или 3 вижа сыра
	all_weight = 0
	for i in self.__resources:
	    if i.get_date().date() != self.__resources[-1].get_date().date():
		all_weight += i.get_weight()
	return float("{0:.3f}".format(float(all_weight) / delta_days))

    @classmethod
    def base_function_types(cls, fns_cheque_element):
	words = u"сыр творог молоко йогурт сметана шоколад томат"
	words = words.upper()
	return_words = set()
	for word in words.split():
	    if word in fns_cheque_element.get_title():
		return_words.add(word)
	return return_words

    def days_future(self):
	"""
	Нас сколько дней хватит последней покупки
	"""
	#TODO уйти от delta_days считать наоснове интервалов
	#delta_days = self.delta_days()
	delta = self.__average_weight_per_day_in_during_period_without_last()
	#days_continue_for_last_buy = self.__resources[0].get_weight() / delta
	#days_continue_for_last_buy = self.__resources[-1].get_weight() / delta

	last_day_weight = 0
	for i in self.__resources:
	    if i.get_date().date() == self.__resources[-1].get_date().date():
		last_day_weight += i.get_weight()
	days_continue_for_last_buy = last_day_weight / delta

	print '==', delta, last_day_weight
	return float("{0:.3f}".format(days_continue_for_last_buy))

    def delta_days(self):
	delta_days = self.__last_date() - self.__first_date()
	return delta_days.days

    def __first_date(self):
	return sorted(self.__resources, key = lambda x : x.get_date())[0].get_date()

    def __init__(self, resources):
	"""
	проверить что все потребление идет впорядке убывания
	    пробую исправить на возрасающий порядо
		пробую исправить на возрасающий порядок
	""" 
	self.__resources = sorted(resources, key = lambda x : x.get_date())

    def __last_date(self):
	return datetime.strptime("2020-06-06T10:00:00", '%Y-%m-%dT%H:%M:%S')
	return "2020-06-06T10:00:00"

    def product_cards(self):
	"""
	формируем карточки продуктов на омнове связей или из ресурсов или ...

	Пока ищем карточки продуктов с словами которые содержутся в названии ресурсов
	"""
	title_parts = []
	for r in self.__resources:
	    title_parts.extend(r.get_title().split(' '))

	return ProductCard.find_by_text(' '.join(title_parts))

	product_cards = []
	for part in title_parts:
	    if part in ['SPAR']:
		continue
	    for product_card in ProductCard.objects.filter(title__icontains=part):
		product_cards.append(product_card)

	return set(product_cards)
	#return set([ProductCard.objects.get(id=2), ProductCard.objects.get(id=1), ProductCard.objects.get(id=3)])

    def __last_buy_date(self):
	"""
	дата последней покупки	
	"""
	return sorted(self.__resources, key = lambda x : x.get_date())[-1].get_date()

    @classmethod
    def save_functions_with_base_function_types(cls, base_function_types):
	#создаем недостающие базовые функции 
	for base_function_type in base_function_types:
	    if not PredictionLinearFunction.objects.filter(base_type=base_function_type).count():
		f = PredictionLinearFunction(base_type=base_function_type)
		f.save()

    def without_last_delta_days(self):
	delta_days = self.__last_buy_date() - self.__first_date()
	return delta_days.days


