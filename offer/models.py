# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from product_card.models import ProductCard
from cheque.models import FNSCheque, FNSChequeElement

# Create your models here.

class Offer(object):
    def __init__(self):
        #TODO что где когда сколько - простой оффер на одну едницу продукции
        self.__product = {}
        self.__datetime = {}
        self.__showcase = {}
        self.__price = {}

#class ProductCard(models.Model):
class Offer(models.Model):
    """
    Оффер это простое предлодение одной из витрин.

    Товар, цена, дата фиксации цены(или по фото или чек), витрина (магазин или странца сайта)
    """

    product_card = models.ForeignKey(ProductCard)
    datetime_create = models.DateTimeField(blank=True, auto_now_add = True)
    datetime = models.DateTimeField(blank=True, null=True) 
    price = models.SmallIntegerField()
    showcase = models.CharField(blank=True, max_length=254)

    def __str__(self):
        #return "%s %s %s %s" % (str(self.price), self.product_card, str(self.datetime), self.showcase.encode('utf8'))
        #return "%s %s %s" % (str(self.price), str(self.datetime), self.showcase)
        return u"%s %s %s" % (str(self.price), str(self.datetime), self.product_card.id) 
        #return "%s" % (str(self.price), )

class ChequeOffer(object):

    @classmethod
    def analytics_last_min_max_price(cls, offers):
	split_by_offer_groups = []
	groups = {}
	for offer in sorted(offers, key = lambda x : x['datetime']['update']):
	    key = offer['product']['title'] + ' ' + (offer['showcase']['address'] if offer['showcase']['address'] else '')
	    #key = offer['product']['title'].encode('utf8') + u' ' + (offer['showcase']['address'].encode('utf8') if offer['showcase']['address'] else '')
	    if not groups.get(key):
		groups[key] = []
	    groups[key].append(offer)
	for k in groups.keys():
	    split_by_offer_groups.append(groups[k])

	#self.assertEqual([], split_by_offer_groups)

	#3) формируем для каждого 100% совпадения названия соответствующую матрицу из описания с разбивкой по диапазонам.

	offer_analytics = []
	for g in split_by_offer_groups: #100% совпадение навзание и адреса
	    #последний по дате оффер, минимальный, и максимальный за последнюю неделю/месяц/квартал/год/все время

	    g = sorted(g, key = lambda x : x['datetime']['update'])
	    last_offer = g[-1]

	    g = sorted(g, key = lambda x : x['price']['per_one_gram'])
	    min_offer = g[0]
	    max_offer = g[-1]

	    offer_analytics.append({
		u'product': {
		    u'title': g[0]['product']['title'],
		},
		u'showcase': {
		    u'address': g[0]['showcase']['address'],
		},
		u'price_analytics': {
		    u'last': last_offer['price'],
		    u'min': min_offer['price'],
		    u'max': max_offer['price'],
		},
                u'last_datetime': last_offer['datetime']['update'],
                u'count': len(g),
	    })

	offer_analytics = sorted(offer_analytics, key = lambda x : x['product']['title'])
	return offer_analytics

    @classmethod
    def find(cls, text):
        offers = []
        for e in FNSChequeElement.objects.filter(name__contains=text):
            offers.append({
                'product': {
                    'title': e.name,
                },
                'datetime': {
                    #'update': e.fns_cheque.get_datetime(),
                    'update': e.get_datetime(),
                },
                'showcase': {
                    #'title': 'Москва, кремль'
                    'address': e.get_address(),
                },
                'price': {
                    'one': e.price,
                    'per_one_gram': e.get_price_per_one_gram()
                },
            })
        return offers


