# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Element(object):
    def get_weight(self):
        return self.__weight
        #return self.__weight if self.__weight else self.__voluem

    def get_date(self):
        return self.__date

    def __init__(self, date, weight):
        self.__date = date
        self.__weight = weight

    def __unicode__(self):
        return u"%s -> %s" % (self.__date, self.__weight)

#class Prediction(models.Model): 
class Prediction(object): 
    """
    Каласс для рассчета потребелния
    """

    @classmethod
    #def average_weight_per_day_in_cluster_products_during_period_v1(cls, elements, delta_days):
    def average_weight_per_day_in_during_period(cls, resources, delta_days):
	all_weight = sum(map(lambda x: float(x.get_weight()), resources))
	return float("{0:.2f}".format(float(all_weight) / delta_days))


