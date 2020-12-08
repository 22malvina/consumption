# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from product_card.models import ProductCard
from cheque.models import ChequeFNSElement
from datetime import datetime


class PredictionLinearFunction(models.Model):
    title = models.CharField(blank=True, max_length=254)
    cheque_elements = models.ManyToManyField(ChequeFNSElement)
    #product_card = models.ForeignKey(ProductCard)
    datetime_create = models.DateTimeField(blank=True, auto_now_add = True)
    base_type = models.CharField(blank=True, max_length=254)

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
	    for product_card in ProductCard.objects.filter(title__contains=part):
		product_cards.append(product_card)

	return set(product_cards)
	#return set([ProductCard.objects.get(id=2), ProductCard.objects.get(id=1), ProductCard.objects.get(id=3)])

    def __last_buy_date(self):
	"""
	дата последней покупки	
	"""
	return sorted(self.__resources, key = lambda x : x.get_date())[-1].get_date()

    def without_last_delta_days(self):
	delta_days = self.__last_buy_date() - self.__first_date()
	return delta_days.days


