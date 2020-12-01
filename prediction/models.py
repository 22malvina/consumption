# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from product_card.models import ProductCard


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
	return float("{0:.2f}".format(float(all_weight) / delta_days))

class PredictionLinear(object):
    """
    Класс рассчета линейного потребления

	ресурсы идут в порядке от от послежнего к самому раннему
    """
    def average_weight_per_day_in_during_period(self, delta_days):
	all_weight = sum(map(lambda x: float(x.get_weight()), self.__resources))
	return float("{0:.2f}".format(float(all_weight) / delta_days))

    def __average_weight_per_day_in_during_period_without_last(self, delta_days):
	all_weight = sum(map(lambda x: float(x.get_weight()), self.__resources[1:]))
	return float("{0:.2f}".format(float(all_weight) / delta_days))

    def days_future(self, delta_days):
	#TODO уйти от delta_days считать наоснове интервалов
	delta = self.__average_weight_per_day_in_during_period_without_last(delta_days)
	days_continue_for_last_buy = self.__resources[0].get_weight() / delta
	return days_continue_for_last_buy

    def __init__(self, resources):
	"""
	проверить что все потребление идет впорядке убывания
	""" 
	self.__resources = resources

    def product_cards(self):
	"""
	формируем карточки продуктов на омнове связей или из ресурсов или ...
	"""
	title_parts = []
	for r in self.__resources:
	    title_parts.extend(r.get_title().split(' '))

	product_cards = []
	for part in title_parts:
	    if part in ['SPAR']:
		continue
	    for product_card in ProductCard.objects.filter(title__contains=part):
		product_cards.append(product_card)

	return set(product_cards)
	#return set([ProductCard.objects.get(id=2), ProductCard.objects.get(id=1), ProductCard.objects.get(id=3)])

