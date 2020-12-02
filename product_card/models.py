# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


#from datetime import date
#from datetime import datetime
#from datetime import timedelta
#
#from django.conf import settings
#
#
#from account.models import Account
#
#import json
#
#import urllib
##import urllib2
#import urllib2, base64
#import pytz
#import re
#
#import time

class CatigoryTree(models.Model):
    #11 групп продуктов:  хлебные продукты (хлеб и макаронные изделия в пересчете на муку, мука, крупы, бобовые);картофель;овощи и бахчевые (капуста, огурцы, помидоры, морковь, свекла, лук);свежие фрукты (яблоки, апельсины, виноград, бананы);сахар и кондитерские изделия;мясопродукты (мясо говядины, баранины, свинины, птицы);рыбопродукты (рыба свежая, сельдь соленая);молоко и молокопродукты (молоко, сметана, масло сливочное, сыр, творог, кисломолочные продукты);яйца;растительное масло, маргарин и другие жиры;прочие продукты (соль, чай и специи).

    parent = models.ForeignKey('self', blank=True, null=True)
    title = models.CharField(blank=True, max_length=254)

    def __create_base_catigory():
        """ для первоночальной инициализации"""
        CatigoryTree.objects.create(id=1, title=u'хлебные продукты (хлеб и макаронные изделия в пересчете на муку, мука, крупы, бобовые,   вермишель, батон, крупа, лапша, кускус, киноа, макарон)')
        CatigoryTree.objects.create(id=2, title=u'картофель')
        CatigoryTree.objects.create(id=3, title=u'овощи и бахчевые (капуста, огурцы, помидоры, морковь, свекла, лук,  чеснок, томат, редис, авокадо, перец, укроп, сельдерей)')
        CatigoryTree.objects.create(id=4, title=u'вежие фрукты (яблоки, апельсины, виноград, банан,  клубника, лимон, киви, чернослив, мандарин, помело)')
        CatigoryTree.objects.create(id=5, title=u'сахар и кондитерские изделияяя (шоколад конфеты зефир,  печенье)')  # изделияяя - чтобы не было совпадений - иакаронные изделия
        CatigoryTree.objects.create(id=6, title=u'мясопродукты (мясо говядины, баранины, свинины, птицы,   сосиски, колбаса, пельмени)')
        CatigoryTree.objects.create(id=7, title=u'рыбопродукты (рыба свежая, сельдь соленая,  тунец, икра, лосос, форел, креветк)')
        CatigoryTree.objects.create(id=8, title=u'молоко и молокопродукты(молоко, сметана, масло сливочное, сыр, творог, кисломолочные продукты,  кефир, йогурт, сливки, сырок)')
        CatigoryTree.objects.create(id=9, title=u'яйца (яйцо)')
        CatigoryTree.objects.create(id=10, title=u'растительное масло, маргарин и другие жиры,  майонез, соус')
        CatigoryTree.objects.create(id=11, title=u'прочие продукты (соль, чай и специи,  мед, орех, чипсы)')

    def __create_sub_catigory():
        """Для первоночальной инициализации"""
        # создаем группы, и подгруппы
        for c in CatigoryTree.objects.all():
            for word in c.title.split():
                word = word.replace(',','').replace('.','').replace('(','').replace(')','')
                word = word.upper()
                if len(word) > 2:
                    CatigoryTree.objects.create(title=word, parent=c)
    @staticmethod
    def init_base():
        """Первоночальная инициализация"""
        __create_base_catigory()
        __create_sub_catigory()

    def __unicode__(self):
        return u"%s -> %s" % (self.title, self.parent)



class ProductCard(models.Model):
    """
    Обогощенная информация по продуктам.
    Нужна для того чтобы пользовптнль вместе с чеком не вбивал фотографии покупки, ее состав, и характеристик.
        А просто выбрать подходящую на его взгляд обогощенную информацию.
    Таким образом не надо знать какой точно год выпуска или партия - пользовтель сам решит.
        Ему можно лишь помочь сделать автоматичекскую рекомендацию.

    Т.е. после того как данный товар заведен, менять его нельзя, так как те места где он используется уже рассчитывают на это(пример с цветами айфона).
    и значит нужно заводить всегда новую информацию о товаре и к новым продуктам предлагать более новую, а старым предлагать обновить основную привзяку
        или позволить создавтаь новые.

    Штрих код можно просить фотографировать и привязвать к позиции в чеке для более быстрого определения продукции.
    """

    parent = models.ForeignKey('self', blank=True, null=True)
    datetime_create = models.DateTimeField(blank=True, auto_now_add = True) # так как карточки не изменяются то дата создания карточки может быть как то связана с началом ее потребелния
    title = models.CharField(blank=True, max_length=254)
    barcode = models.CharField(blank=True, max_length=254) # щтрихкод
    weight = models.SmallIntegerField(blank=True, null=True) # вес содержимого
    is_packed = models.NullBooleanField() # товар продается не на вес(пачкой, блок, кансервная тара т.е. уже фасованный - не делимая - тельзя продать пол банки гороха)
    #composition = models.TextField(blank=True, ) # состав
    #image_main_v1 = models.CharField(blank=True, max_length=254)
    #instruction = models.TextField(blank=True, ) # инструкция

    catigory_tree = models.ForeignKey(CatigoryTree, blank=True, null=True)
    catigory_sub_tree = models.ForeignKey(CatigoryTree, blank=True, null=True, related_name="product_info_2_catigory_sub_tree")

    @classmethod
    def find_by_text(cls, text):
	title_parts = text.split(' ')

	product_cards = set()
	for part in title_parts:
	    if part in ['SPAR']:
		continue
	    for product_card in ProductCard.objects.filter(title__contains=part):
		product_cards.add(product_card)

	return product_cards

    @classmethod
    def update_catigory_and_sub_catigory_for_all_products(cls):
	# привязываем прдгрыы к продуктам
	for p in ProductCard.objects.all():
	    for c in CatigoryTree.objects.all():
		for word in c.title.split():
		    word = word.replace(',','').replace('.','').replace('(','').replace(')','')
		    word = word.upper()
		    if len(word) > 2:
			if p.title.find(word) != -1:
			    if c.parent:
				p.catigory_sub_tree = c
			    else:
				p.catigory_tree = c
			    p.save()

    def __str__(self):
        return self.title.encode('utf8')




