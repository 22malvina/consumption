# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from cheque.models import QRCodeReader, FNSCheque, ImportProverkachekaComFormatLikeFNS, FNSChequeElement
import json
import urllib
import urllib2
#import  base64
from django.conf import settings

class Telegram(object):
    @classmethod
    def __add_new_cheque_by_qr_text_and_send_answer_to_telegram_chat(cls, company, qr_text, chat_id):
        #account = None
        #if FNSCheque.has_cheque_with_fiscal_params():
        #    new_message = {
        #        u'chat_id': chat_id,
        #        u'text': u'Такой чек уже существует 1',
        #    }
        #    Telegram.send_message(new_message)
        #    return

	fns_cheque = FNSCheque.create_fns_cheque_from_qr_text(qr_text, company)
	fns_cheque.save()
        fns_cheque_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params('', qr_text)
        account = None
	FNSCheque.update_cheque_from_json(fns_cheque, fns_cheque_json)

        if fns_cheque:
            new_message = {
                'chat_id': chat_id,
                'text': u'Здесь будет в JSON чека полученный от ФНС',
            }
            Telegram.send_message(new_message)
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' руб. сохранен.'
            }
            Telegram.send_message(new_message)
        else:
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Не смогли загрузить ваш чек :' + qr_text,
            }
            Telegram.send_message(new_message)

    @classmethod
    def is_new_user(cls):
        return False

    @classmethod
    def proccess_message(cls, company, chat_id, message):
#	full_message = {}
#
#	chat_id = full_message['message']['chat']['id']
#	message = full_message['message']['text']
#	#telegram_user_id = message['message']['from']['id']
#	#first_name = message['message']['from'].get('first_name', '')
#	#last_name = message['message']['from'].get('last_name', '')
#	#language_code = message['message']['from'].get('language_code', '')
	
        if Telegram.is_new_user() and not message.find('/start') >= 0 and not message.find('/help') >= 0:
            new_message = {
                u'chat_id': chat_id,
                u'text': u'FYI: Отправьте /help чтобы получить справку.',
            }
	    Telegram.send_message(new_message)

        if message.find('/start') >= 0:
            if is_new:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Приветсвую! Отправьте /help чтобы получить справку.',
                }
            else:
                new_message = {
                    'chat_id': chat_id,
                    'text': u'И снова здравствуйте! Отправьте /help чтобы получить справку.'
                }
	    Telegram.send_message(new_message)
        elif message.find('/help') >= 0 or message.find('Help') >= 0 or message.find('HELP') >= 0 or message.find('help') >= 0:
            new_message = {
                'chat_id': chat_id,
                'text': u"""Help : Здравствуйте, я могу рассказать вам как можно сэкономить при ежедневных походах в магазин.
А также помогу проверить чеки пробитые в магазинах.
Чтобы загрузить чек отправьте, распознаый QR код и укажите вначале /qrcode - пример:
/qrcode t=20200524T125600&s=849.33&fn=9285000100127361&i=115180&fp=1513716805&n=1
или просто текст QR кода:
t=20200524T125600&s=849.33&fn=9285000100127361&i=115180&fp=1513716805&n=1
Чтобы узнать что сегодня следует купить отправьте
/basket_today
/list список всех покупок
                """
            }
	    Telegram.send_message(new_message)
        elif message.find('/qrcode') >= 0 or message.find('Qrcode') >= 0 or \
	    message.find('qr') >= 0 or message.find('Qr') >= 0:
            request = message.split(' ')
            if len(request) > 1:
                qr_text = request[1]
		Telegram.__add_new_cheque_by_qr_text_and_send_answer_to_telegram_chat(company, qr_text, chat_id)
	elif (
		message.find('t') >= 0 and \
	        message.find('s') >= 0 and \
		message.find('fn') >= 0 and \
		message.find('fp') >= 0 and \
		message.find('i') >= 0
	    ):
            qr_text = message
	    Telegram.__add_new_cheque_by_qr_text_and_send_answer_to_telegram_chat(company, qr_text, chat_id)
        elif message.find('/basket_today') >= 0 or message.find('Basket_today') >= 0:
	    new_message = {
		u'chat_id': chat_id,
		u'text': {
		    u'Рекомендуем к покупке сегодня': new_recomendate,
		    u'Среднее потребеление в день': average_weight_per_day,
		},
	    }
	    Telegram.send_message(new_message)
        elif message.find('/list') >= 0 or message.find('List') >= 0:
            cheques = []
            for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime'):
                cheques.append({
                    u'totalSum': str(cheque.fns_totalSum),
                    u'see': u'/cheque ' + str(cheque.id),
                    #u'date': u'%s' % str(cheque.fns_dateTime.date()),
                    u'date': u'%s' % str(cheque.fns_dateTime),
                })
	    new_message = {
		u'chat_id': chat_id,
		u'text': {
		    u'Всего покупок': len(cheques),
		    u'Ваши покупки': cheques,
		},
	    }
	    Telegram.send_message(new_message)
        elif message.find('/cheque') >= 0 or message.find('Cheque') >= 0:
            request = message.split(' ')
            if len(request) > 1:
                cheque_id = request[1]
            cheque = FNSCheque.objects.get(company=company, id=cheque_id)
            elements = []
            for e in FNSChequeElement.objects.filter(fns_cheque=cheque):
                elements.append([e.get_title(), str(e.get_price()), str(e.get_quantity()), str(e.get_sum())])
	    new_message = {
		u'chat_id': chat_id,
		u'text': {
		    u'Общая сумма': cheque.fns_totalSum,
		    u'Дата покупки': cheque.fns_dateTime,
		    u'Всего товаров в чек': str(len(elements)),
		    u'Ваши покупки': elements,
		},
	    }
	    Telegram.send_message(new_message)

    @classmethod
    def send_message(cls, message):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        url_api = "https://api.telegram.org/bot%s/" % bot_token
        request_timeout = 10

        print message['chat_id']
        #print message['text'].encode('utf8')

        if isinstance(message['text'], (list, dict, tuple)):
            print json.dumps(message['text'], ensure_ascii=False).encode('utf8'),
            params_v = {
                u'chat_id': message['chat_id'],
                u'text': json.dumps(message['text'], ensure_ascii=False).encode('utf8'),
            }
        elif isinstance(message['text'], unicode):
            print message['text'].encode('utf-8'),
            params_v = {
                u'chat_id': message['chat_id'],
                u'text': message['text'].encode('utf-8'),
            }
        else:
            print 'Error: process Telegram'
            print message['text']
            params_v = {
                u'chat_id': message['chat_id'],
                u'text': message['text'],
            }
 
        data = urllib.urlencode(params_v)
        request = urllib2.Request(url=url_api + 'sendMessage', data=data)
        try:
            responce = urllib2.urlopen(request, timeout=request_timeout)
            print "result code: " + str(responce.getcode()) 
            ##data = weburl.read()
            ##print data
            #data_r = json.load(responce)
            #print data_r
        except:
            import traceback
            traceback.print_exc()

        #responce = urllib2.urlopen(request, timeout=request_timeout)
#	print "result code: " + str(responce.getcode()) 
#	#data = weburl.read()
#	#print data
#	data_r = json.load(responce)
#	print data_r


