# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from cheque.models import QRCodeReader, FNSCheque, ImportProverkachekaComFormatLikeFNS, FNSChequeElement, ShowcasesCategory
import json
import urllib
import urllib2
#import  base64
from django.conf import settings
from company.models import Employee, Company
from offer.models import ChequeOffer

from datetime import datetime
import re
import time

from sentry_sdk import capture_exception, capture_message

class ProcessedMessage(models.Model):
    json = models.TextField(blank=True, )
    message_id = models.CharField(blank=True, max_length=254) # ид собщения в рамках чата
    update_id = models.CharField(blank=True, max_length=254) # использовать при веб хуках

    def __unicode__(self):
        return u"U: %s, M: %s, JSON: %s" % (self.update_id, self.message_id, self.json)
 
class Telegram(object):
#message with photo
#{u'message': {
#    u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826},
#    u'photo': [
#        {u'width': 240, u'height': 320, u'file_id': u'AgACAgIAAxkBAAIOMF_boXZYtLpffoHzg47fU0v06wNUAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA20AAz1sBQABHgQ', u'file_unique_id': u'AQADmo2gli4AAz1sBQAB', u'file_size': 11934},
#        {u'width': 600, u'height': 800, u'file_id': u'AgACAgIAAxkBAAIOMF_boXZYtLpffoHzg47fU0v06wNUAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3gAAz9sBQABHgQ', u'file_unique_id': u'AQADmo2gli4AAz9sBQAB', u'file_size': 52646},
#        {u'width': 960, u'height': 1280, u'file_id': u'AgACAgIAAxkBAAIOMF_boXZYtLpffoHzg47fU0v06wNUAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ', u'file_unique_id': u'AQADmo2gli4AAz5sBQAB', u'file_size': 85969}
#    ], 
#    u'chat': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'type': u'private', u'id': 383332826},
#    u'date': 1608229238, 
#    u'message_id': 3632,
#    u'media_group_id': u'12865833907857842'},
#u'update_id': 397005490}


# не сжатаая картинка
#{u'message': {
#    u'date': 1608372565, 
#    u'document': {
#        u'thumb': {u'width': 240, u'height': 320, u'file_id': u'AAMCAgADGQEAAg97X93RVVVjKoQuKBZ1MHsjhpb0elcAAuQKAAKS4_FKg_bK000rJ0ussnOdLgADAQAHbQADDVEAAh4E', u'file_unique_id': u'AQADrLJznS4AAw1RAAI', u'file_size': 10416}, 
#        u'file_name': u'photo_2020-12-17_20-57-39.jpg', 
#        u'mime_type': u'image/jpeg', 
#        u'file_size': 54462, 
#        u'file_unique_id': u'AgAD5AoAApLj8Uo', 
#        u'file_id': u'BQACAgIAAxkBAAIPe1_d0VVVYyqELigWdTB7I4aW9HpXAALkCgACkuPxSoP2ytNNKydLHgQ'    
#    }, 
#    u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, 
#    u'message_id': 3963, 
#    u'chat': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'type': u'private', u'id': 383332826}
#}, 
#u'update_id': 397005609}


#https://api.telegram.org/botXXXXX:YYYYYYY/getFile?file_id=AgACAgIAAxkBAAIOLV_bm_ADUaQ8SPjcyA1Ht44OVxQsAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ
#{
#    "ok": true,
#    "result": {
#        "file_id": "AgACAgIAAxkBAAIOMF_boXZYtLpffoHzg47fU0v06wNUAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ",
#        "file_unique_id": "AQADmo2gli4AAz5sBQAB",
#        "file_size": 85969,
#        "file_path": "photos/file_1.jpg"
#    }
#}

#https://api.telegram.org/file/botXXXXXXX:YYYYYYYY/photos/file_1.jpg
#Получаем фаил

#TODO добавили бота в группу
#{u'message': {
#   u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, 
#   u'chat': {u'all_members_are_administrators': True, u'type': u'group', u'id': -419745626, u'title': u'\u041c\u043e\u044f \u0441\u0435\u043c\u044c\u044f'}
#   u'date': 1608311909, 
#   u'message_id': 3837, 
#   u'group_chat_created': True, 
#   }, 
#u'update_id': 397005544}

#отключил настройки приватности в BotFather  и теперь бот получет все сообщения из груп в которые его боавили
#{u'message': {
#    u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826},
#    u'chat': {u'all_members_are_administrators': True, u'type': u'group', u'id': -419745626, u'title': u'\u041c\u043e\u044f \u0441\u0435\u043c\u044c\u044f'}, 
#    u'date': 1608313264, 
#    u'message_id': 3843
#    u'text': u'/help', 
#    u'entities': [{u'length': 5, u'type': u'bot_command', u'offset': 0}], 
#    }, 
#u'update_id': 397005550}

# обычное сообщение
#{u'message': {
#    u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, 
#    u'chat': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'type': u'private', u'id': 383332826}, 
#    u'date': 1608313675, 
#    u'message_id': 3850, 
#    u'text': u'1111', 
#    }
#u'update_id': 397005554}

#чек с картинкой
#{u'message': {
#u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, 
#u'photo': [
#    {u'width': 240, u'height': 320, u'file_id': u'AgACAgIAAxkBAAIPbF_dzpGuoy9ET2emn0PVEIYnQaXBAALtrzEbkuPxStG3PlyMT54rerSUly4AAwEAAwIAA20AAxOnBAABHgQ', u'file_unique_id': u'AQADerSUly4AAxOnBAAB', u'file_size': 11966}, 
#    {u'width': 600, u'height': 800, u'file_id': u'AgACAgIAAxkBAAIPbF_dzpGuoy9ET2emn0PVEIYnQaXBAALtrzEbkuPxStG3PlyMT54rerSUly4AAwEAAwIAA3gAAxSnBAABHgQ', u'file_unique_id': u'AQADerSUly4AAxSnBAAB', u'file_size': 52344}, 
#    {u'width': 960, u'height': 1280, u'file_id': u'AgACAgIAAxkBAAIPbF_dzpGuoy9ET2emn0PVEIYnQaXBAALtrzEbkuPxStG3PlyMT54rerSUly4AAwEAAwIAA3kAAxKnBAABHgQ', u'file_unique_id': u'AQADerSUly4AAxKnBAAB', u'file_size': 64628}], 
#u'caption_entities': [
#    {u'length': 13, u'type': u'bot_command', u'offset': 0}], 
#u'caption': u'/cheque169756', 
#u'chat': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'type': u'private', u'id': 383332826}, 
#u'date': 1608371857, 
#u'message_id': 3948}, 
#u'update_id': 397005604}


#2 раздельные картинки

#{u'message': {
#   u'date': 1608371563, 
#   u'photo': 
#   u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, 
#   u'message_id': 3944, u'chat': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'type': u'private', u'id': 383332826}
#}, 
#u'update_id': 397005602}
#{u'message': {
#   u'date': 1608371567,
#   u'photo': ,
#   u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, 
#   u'message_id': 3947, 
#   u'chat': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'type': u'private', u'id': 383332826}
#}, 
#u'update_id': 397005603}


# 2 слитные картинки(групой)

#{u'message': {
#    u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, 
#    u'photo': 
#    u'caption': u'test test test', 
#    u'chat': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'type': u'private', u'id': 383332826}, 
#    u'date': 1608372027, 
#    u'message_id': 3957, 
#    u'media_group_id': u'12866976216359970'}, 
#u'update_id': 397005607}
#{u'message': {
#    u'from': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, 
#    u'photo': , 
#    u'chat': {u'username': u'atsurkov', u'first_name': u'Art', u'last_name': u'Ts', u'type': u'private', u'id': 383332826}, 
#    u'date': 1608372027, 
#    u'message_id': 3958, 
#    u'media_group_id': u'12866976216359970'}, 
#u'update_id': 397005608}

    @classmethod
    def __add_new_cheque_by_qr_text_and_send_answer_to_telegram_chat(cls, company, message_text, chat_id):
        if not cls.is_it_contains_qr_text(message_text):
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Данных параметров не достаточно для проверки чека.',
            }
            Telegram.send_message(new_message)

            capture_message('Error: Not find necessary params from user','fatal')
            return

        for text in message_text.split(' '):
            if QRCodeReader.is_it_qr_text(text):
                cls.__add_new_cheque_by_qr_text_and_send_answer_to_telegram_chat_1(company, text, chat_id)

    @classmethod
    def __add_new_cheque_by_qr_text_and_send_answer_to_telegram_chat_1(cls, company, qr_text, chat_id):
        if FNSCheque.has_cheque_with_qr_text(company, qr_text):
            cheque = FNSCheque.get_cheque_with_qr_text(company, qr_text)
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Такой чек уже существует в данном чате! /cheque_' + str(cheque.id),
            }
            Telegram.send_message(new_message)
            cls.__send_message_include_offer_with_best_recomended_price_v2(company, chat_id, cheque)
            return
        else:
            fns_cheque = FNSCheque.create_save_update_fns_cheque_from_proverkacheka_com(qr_text, company)

        if fns_cheque:
            fns_cheque = FNSCheque.objects.get(id=fns_cheque.id)
            #new_message = {
            #    'chat_id': chat_id,
            #    'text': u'Здесь будет в JSON чека полученный от ФНС',
            #}
            #Telegram.send_message(new_message)
            new_message = {
                u'chat_id': chat_id,
                #u'text': u'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' \u20bd сохранен.'
                'text': cls.__get_answer_string_when_add_cheque(fns_cheque),
            }
            Telegram.send_message(new_message)
            cls.__send_message_include_offer_with_best_recomended_price_v2(company, chat_id, fns_cheque)
        else:
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Не смогли загрузить ваш чек :' + qr_text,
            }
            capture_message('Error: Not load your cheque','fatal')
            Telegram.send_message(new_message)
 
    @classmethod
    def __calc_sum_for_cheque_with_new_offer(cls, cheque, element_2_elements):
        summ = 0
        for k in element_2_elements.keys():
            element_2_elements[k].sort(key = lambda x : x.get_price_per_one_gram() if x.get_price_per_one_gram() else x.get_price())
            #TODO не верно работает
            if len(element_2_elements[k]):
                summ += float(element_2_elements[k][0].get_price())/100 * float(k.get_quantity())
        return summ

    @classmethod
    def __difference_percent_total(cls, cheque, summ):
        return(
            (float(cheque.fns_totalSum)/100 - float(summ)),
            (int((((float(cheque.fns_totalSum)/100) - float(summ)) / (float(cheque.fns_totalSum)/100))*100)),
            (float(cheque.fns_totalSum)/100)
        )

    @classmethod
    def __get_company_for_user(cls, telegram_user_id, chat_id, username, first_name, last_name, language_code, chat_title):
        employees = Employee.objects.filter(telegram_id=telegram_user_id)
        if len(employees) > 1:
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Добрый день, сервис временно не доступен.',
            }
            Telegram.send_message(new_message)
            assert False
        elif len(employees) == 0:
            employee = Employee(title=username, first_name=first_name, last_name=last_name, language_code=language_code, telegram_id=telegram_user_id)
            employee.save()

            companys = Company.objects.filter(telegram_chat_id=chat_id)
            if len(companys) > 1:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Добрый день, сервис временно не доступен.',
                }
                Telegram.send_message(new_message)
                assert False
            elif len(companys) == 1:
                company = companys[0]
                company.employees.add(employee)
            elif len(companys) == 0:
                company = Company(title=chat_title, telegram_chat_id=chat_id)
                company.save()
                company.employees.add(employee)
            else:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Добрый день, сервис временно не доступен.',
                }
                Telegram.send_message(new_message)
                assert False
            #company = Company(title=chat_title, telegram_chat_id=chat_id)
            #company.save()
            #company.employees.add(employee)
            #new_message = {
            #    u'chat_id': chat_id,
            #    u'text': u'Приветсвую! Отправьте /help чтобы получить справку.',
            #}
            #Telegram.send_message(new_message)
        elif len(employees) == 1:
            employee = employees[0]
            companys = Company.objects.filter(employees=employee, telegram_chat_id=chat_id)
            if len(companys) > 1:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Добрый день, сервис временно не доступен.',
                }
                Telegram.send_message(new_message)
                assert False
            elif len(companys) == 1:
                company = companys[0]
            elif len(companys) == 0:
                #new_message = {
                #    u'chat_id': chat_id,
                #    u'text': u'Добрый день, сервис временно не доступен.',
                #}
                #Telegram.send_message(new_message)
                #print telegram_user_id, chat_id
                #assert False
                companys = Company.objects.filter(telegram_chat_id=chat_id)
                if len(companys) > 1:
                    new_message = {
                        u'chat_id': chat_id,
                        u'text': u'Добрый день, сервис временно не доступен.',
                    }
                    Telegram.send_message(new_message)
                    assert False
                elif len(companys) == 1:
                    company = companys[0]
                    company.employees.add(employee)
                elif len(companys) == 0:
                    company = Company(title=chat_title, telegram_chat_id=chat_id)
                    company.save()
                    company.employees.add(employee)
                else:
                    new_message = {
                        u'chat_id': chat_id,
                        u'text': u'Добрый день, сервис временно не доступен.',
                    }
                    Telegram.send_message(new_message)
                    assert False
                #new_message = {
                #    u'chat_id': chat_id,
                #    u'text': u'Приветсвую! Теперь вы можете использовать функционал в данной группе',
                #}
                #Telegram.send_message(new_message)
            else:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Добрый день, сервис временно не доступен.',
                }
                Telegram.send_message(new_message)
                assert False
        else:
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Добрый день, сервис временно не доступен.',
            }
            Telegram.send_message(new_message)
            assert False
        return company

    @classmethod
    def get_file(cls, file_path):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        url_api = "https://api.telegram.org/file/bot%s/" % bot_token
        request_timeout = 59

        request = urllib2.Request(url=url_api + str(file_path))
        responce = urllib2.urlopen(request, timeout=request_timeout)
	print "result code: " + str(responce.getcode()) 
        return responce.read()

    @classmethod
    def get_file_info(cls, file_id):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        url_api = "https://api.telegram.org/bot%s/" % bot_token
        request_timeout = 59

        request = urllib2.Request(url=url_api + 'getFile?file_id=' + str(file_id))
        responce = urllib2.urlopen(request, timeout=request_timeout)
	print "result code: " + str(responce.getcode()) 
	responce = json.load(responce)

        messages = []
        if responce['ok']:
            return responce['result']
        else:
            assert False
        return messages

    def __get_filnal_price(o):
        return (float(o["price"]["per_one_gram"])/100 if o["price"]["per_one_gram"] else float(o["price"]["one"])/100)

    @classmethod
    #def get_messages(cls):
    def get_last_messages(cls, more_by_1_than_last_update_id):
        bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        url_api = "https://api.telegram.org/bot%s/" % bot_token
	#telegram_bot_id = getattr(settings, "TELEGRAM_BOT_ID", None)

        # сделаем тайматы отличабщимис яна секунду, а в кроне будем скрипт запсукть каждую минут.
        request_timeout = 59
        long_polling_timeout = 58

        #TODO времено отклчил
        #request = urllib2.Request(url=url_api + 'getUpdates')
        request = urllib2.Request(url=url_api + 'getUpdates?timeout=' + str(long_polling_timeout) + (('&offset=' + more_by_1_than_last_update_id) if more_by_1_than_last_update_id else ''))
        #print request.get_full_url()
        responce = urllib2.urlopen(request, timeout=request_timeout)
	print "result code: " + str(responce.getcode()) 
	responce = json.load(responce)

        messages = []
        if responce['ok']:
            for message in responce['result']:
                print message
                messages.append(message)
        else:
            assert False
        return messages

    @classmethod
    def is_it_contains_qr_text(cls, text):
        for t in text.split(' '):
            if QRCodeReader.is_it_qr_text(t):
                return True
        return False

    @classmethod
    def process_last_messages_from_bot(cls):
        """
        {u'message': {u'date': 1607980137, u'text': u'test', u'from': {u'username': u'artem', u'first_name': u'Art', u'last_name': u'em', u'is_bot': False, u'language_code': u'ru', u'id': 383332826}, u'message_id': 2995, u'chat': {u'username': u'artem', u'first_name': u'Art', u'last_name': u'em', u'type': u'private', u'id': 383332826}}, u'update_id': 397005353}
        """
        last_update_ids = ProcessedMessage.objects.order_by('-update_id')[0:1]
        more_by_1_than_last_update_id = str(int(last_update_ids[0].update_id) + 1) if len(last_update_ids) > 0 else None
        for full_message in cls.get_last_messages(more_by_1_than_last_update_id):
            #TODO надо проверять не обрабатвалось ли это сообщение уже

            if full_message.get('update_id', None) and cls.__was_message_processed(full_message['update_id']):
                print 'Alert: message with update_id =', full_message['update_id'], 'was processed!' 
                continue

            pm = ProcessedMessage(json=json.dumps(full_message, sort_keys=True))
            pm.save()
            if full_message.get('update_id', None):
                pm.update_id = full_message.get('update_id')
                pm.save()

            if not full_message.get('message', False):
                continue

            message_id = full_message['message']['message_id']
            update_id = full_message['update_id']

            #u'chat': {u'all_members_are_administrators': True, u'type': u'group', u'id': -419745626, u'title': u'\u041c\u043e\u044f \u0441\u0435\u043c\u044c\u044f'}, 
            chat_id = full_message['message']['chat']['id']
            if full_message['message']['chat']['type'] == 'group':
                chat_title = full_message['message']['chat'].get('title', '')
            elif full_message['message']['chat']['type'] == 'private':
                chat_title = full_message['message']['chat'].get('username', '')
            else:
                print 'Error: New type chat!'
                assert False

            text = full_message['message'].get('text')

            if text:
                text = text.replace('@' + getattr(settings, "TELEGRAM_BOT_TITLE", None), '')

            telegram_user_id = full_message['message']['from']['id']
            username = full_message['message']['from'].get('username', '')
            first_name = full_message['message']['from'].get('first_name', '')
            last_name = full_message['message']['from'].get('last_name', '')
            language_code = full_message['message']['from'].get('language_code', '')

            company = cls.__get_company_for_user(telegram_user_id, chat_id, username, first_name, last_name, language_code, chat_title)
                       
            if text:
                #TODO если к фото привязан текс то такое фото не боработается
                Telegram.process_message(company, chat_id, text)
                #pm = ProcessedMessage(message_id=message_id, update_id=update_id, json=json.dumps(full_message, sort_keys=True))
                pm.message_id = message_id
                pm.save()
                print 'save'

            elif full_message['message'].get('document'):
                document = full_message['message'].get('document')
                #if not document['mime_type'] == 'image/jpeg':
                #    continue
                file_id = document['file_id']
                if not cls.process_file(company, chat_id, file_id):
                    continue
                pm.message_id = message_id
                pm.save()
                print 'save documen(image)'

            elif full_message['message'].get('photo'):
                #сортируем по размеру чтобы получить самый большой
                photos = full_message['message'].get('photo')
                photos.sort(key = lambda x : int(x['width']))
                bigest_photo = photos[-1]
                file_id = bigest_photo['file_id']
                if not cls.process_file(company, chat_id, file_id):
                    continue
                pm.message_id = message_id
                pm.save()
                print 'save photo'

            else:
                print 'Alert: Not message text.'

    @classmethod
    def __get_answer_string_when_add_cheque(cls, fns_cheque):
        recomended_showcases_category = fns_cheque.get_recomended_showcases_category()
        return 'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' \u20bd приобретенный в "' + fns_cheque.get_shop_info_string() + '" сохранен. \nРасширенная информация по чеку доступна по команде /cheque_' + str(fns_cheque.id) + ' \nТакже вы можете указать категорию места приобретения из списка /cscats_' + str(fns_cheque.id) + ' Или быстро установить категорию "' + recomended_showcases_category.telegram_emoji + ' ' + recomended_showcases_category.title + '" командой /cscat_' + str(fns_cheque.id) + '_' + str(recomended_showcases_category.id)

    @classmethod
    def get_fns_cheque_json_from_proverkacheka_com(cls, new_file):
        #работает
        #curl -F 'qrfile=@AgACAgIAAxkBAAIOLV_bm_ADUaQ8SPjcyA1Ht44OVxQsAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ'  https://proverkacheka.com/check/get

        import requests
        #так работает
        #with open('AgACAgIAAxkBAAIOLV_bm_ADUaQ8SPjcyA1Ht44OVxQsAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ', 'rb') as f:
        #    r = requests.post('https://proverkacheka.com/check/get', files={'qrfile': f})



        #r = requests.post('https://proverkacheka.com/check/get', files={'qrfile': new_file})
        #r = requests.post('https://proverkacheka.com/api/v1/check/get', files={'qrfile': new_file}, data={'qrurl': '', 'qr': '2', 'token': '0.19'})
        r = requests.post('https://proverkacheka.com/api/v1/check/get', files={'qrfile': new_file}, data={'qrurl': '', 'qr': '2', 'token': '0.19'})
        #r = requests.post('https://proverkacheka.com/api/v1/check/get', files={'qrfile': new_file}, data={'qrurl': '', 'qr': '2'})

        #print r.text.encode('utf8')
        #rr = r.json()
        #print r.headers['Content-Type']
        #print r.status_code
        #print r.raise_for_status()  
        if r.status_code == requests.codes.ok:
            decoded_result = r.json()
            return decoded_result
        else:
            capture_message('Error: proverkacheka.com not recognize image','fatal')

            print r.text.encode('utf8')
            return r.text.encode('utf8')
            #non_json_result = r.data
            #print non_json_result.encode('utf8')
        return
        #print rr
        #return rr
        #return json.load(rr)
        #return json.load(r.text.encode('utf8'))



#        #import urllib.request
#        #import urllib.parse
#        from lib.multipart_sender import MultiPartForm
#
#        myfile = new_file
#        form = MultiPartForm()
#        form.add_field('qr', 2)
#        form.add_file('qrfile', 'logo.jpg', fileHandle=myfile)
#        form.make_result()
#
#        url = 'https://proverkacheka.com/check/get'
#        req1 = urllib.request.Request(url)
#        req1.add_header('Content-type', form.get_content_type())
#        req1.add_header('Content-length', len(form.form_data))
#        req1.add_data(form.form_data)
#        fp = urllib.request.urlopen(req1)
#        print(fp.read()) # to view status
#
#
#
#
#        #print new_file
#    
#        request_timeout = 60
#
#        #https://stackoverflow.com/questions/680305/using-multipartposthandler-to-post-form-data-with-python
#        from poster.streaminghttp import register_openers
#        from poster.encode import multipart_encode
#        register_openers()
#        datagen, headers = multipart_encode({'qr': 2, 'qrfile': new_file})
#        #print params_v['document']
#        #request = urllib2.Request(url=url_api + 'sendDocument', data=data, files={'document': json.dumps(message['text'], ensure_ascii=False).encode('utf8')})
#        #request = urllib2.Request(url=url_api + 'sendDocument', files={'document': json.dumps(message['text'], ensure_ascii=False).encode('utf8')})
#        #request = urllib2.Request(url_api + 'sendDocument?chat_id=' + str(message['chat_id']), datagen, headers)
#
#        #artem
#        #request = urllib2.Request('https://proverkacheka.com/check/get', datagen, headers)
#
#        request = urllib2.Request(url='https://proverkacheka.com/check/get', files={'qrfile': new_file})
#
#        responce = urllib2.urlopen(request, timeout=request_timeout)
#        print "result code: " + str(responce.getcode()) 
#        ##data = weburl.read()
#        ##print data
#        data_r = json.load(responce)
#        print data_r
#
#        print data_r['data'].encode('utf8')
#
#
#        return data_r
#
#
#
#        #theRequest = urllib2.Request(theUrl, theFile, theHeaders)('https://proverkacheka.com/check/get', new_file, {'Content-Type': 'text/xml'}).read()
#        #response = urllib2.urlopen(theRequest)
#        #print response.read()
#
#	req = urllib2.Request('https://proverkacheka.com/check/get')
#        da = urllib.urlencode({
#            #'qrraw': 't=20201107T2058&s=63.00&fn=9288000100192401&i=439&fp=2880362760&n=1',
#            #'qrraw': qr_text,
#            'qr': 2,
#            'qrfile': new_file,
#        })
#        #data = urllib2.urlopen(url=req, data=da).read()
#
#        data = urllib2.urlopen('https://proverkacheka.com/check/get', new_file, {'Content-Type': 'text/xml'}).read()
#        print data
#
#        fns_cheque_json = json.loads(data)
#
#        if not type(fns_cheque_json) is dict or not type(fns_cheque_json['data']) is dict:
#            print u'Alert: This is not good JSON!'
#            return
#
#        fns_cheque_json["document"] = {}
#        fns_cheque_json["document"]["receipt"] = fns_cheque_json['data']['json']
#
#        return fns_cheque_json
#
#
##        request = urllib2.Request(url=url_api + 'getUpdates')
##        #request = urllib2.Request(url=url_api + 'getUpdates?timeout=' + str(long_polling_timeout) + (('&offset=' + more_by_1_than_last_update_id) if more_by_1_than_last_update_id else ''))
##        #print request.get_full_url()
##        responce = urllib2.urlopen(request, timeout=request_timeout)
##	print "result code: " + str(responce.getcode()) 
##	responce = json.load(responce)

    @classmethod
    def __get_cat_title(cls, cheque):
        if cheque.showcases_category:
            return cheque.showcases_category.telegram_emoji + ' ' + cheque.showcases_category.title
        return u'\u2754 Другое'

    @classmethod
    def __get_year_month_day(cls, date_time):
        d = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S').date()
        return d
        #return ('0' if d.day <10 else '') + str(d.day) + '.' + ('0' if d.month <10 else '') + str(d.month) + '.' + str(d.year) 

    @classmethod
    def process_file(cls, company, chat_id, file_id):

        file_info = cls.get_file_info(file_id)
        file_path = file_info['file_path']

        new_file = cls.get_file(file_path)

        f = open(file_id, "a")
        f.write(new_file)
        f.close()
        #пока не сохраняем сразу отправляем дальше в проверку чеков

        fns_cheque_json = cls.get_fns_cheque_json_from_proverkacheka_com(new_file)
        if not fns_cheque_json or not type(fns_cheque_json) == dict:
            print 'Error: Not find json' 
            capture_message('Error: Not find json in answer from proverkacheka','fatal')
            cls.__send_error_when_load_photo_with_qr_kode(chat_id, fns_cheque_json)
            return False


        #if fns_cheque_json.get('data'):
        #    import base64
        #    encoded_data = base64.b64decode(fns_cheque_json.get('data'))
        #    print encoded_data.encode('utf8')
        #    print 'Error: Bad json format 2'
        #    return False

        if not fns_cheque_json.get('data') or not type(fns_cheque_json['data']) == dict  or not fns_cheque_json['data'].get('json'):
            print 'Error: Bad json format'
            capture_message('Error: Bad json format in answer from proverkacheka','fatal')
            cls.__send_error_when_load_photo_with_qr_kode(chat_id, fns_cheque_json)
            return False

        #print fns_cheque_json
        fns_cheque_json["document"] = {}
        fns_cheque_json["document"]["receipt"] = fns_cheque_json['data']['json']

        if FNSCheque.has_cheque_with_fns_cheque_json(company, fns_cheque_json):
            cheque = FNSCheque.get_cheque_with_fns_cheque_json(company, fns_cheque_json)
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Такой чек уже существует в данном чате! /cheque_' + str(cheque.id),
            }
            Telegram.send_message(new_message)
            cls.__send_message_include_offer_with_best_recomended_price_v2(company, chat_id, cheque)
            return False

        fns_cheque = FNSCheque(is_manual=False, company=company)
        #TODO проверить что такого чека еще нет в этой окмпании а то получается 2 раза один и тот же чек добавить
        fns_cheque.save()

        #FNSCheque.update_cheque_from_json(fns_cheque, fns_cheque_json)
        fns_cheque.update_cheque_from_json(fns_cheque_json)
        fns_cheque.set_best_category_if_high_rating()

        if fns_cheque:
            fns_cheque = FNSCheque.objects.get(id=fns_cheque.id)

            #new_message = {
            #    'chat_id': chat_id,
            #    'text': u'Здесь будет в JSON чека полученный от ФНС',
            #}
            #Telegram.send_message(new_message)
            new_message = {
                u'chat_id': chat_id,
                #u'text': u'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' \u20bd приобретенный в ' + fns_cheque.get_user() + ' ' + fns_cheque.get_user_inn() + ' ' + fns_cheque.get_address() + ' сохранен. Расширенная информация по чеку доступна по команде /cheque_' + str(fns_cheque.id),
                #u'text': u'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' \u20bd приобретенный в ' + fns_cheque.get_shop_info_string() + ' сохранен. Расширенная информация по чеку доступна по команде /cheque_' + str(fns_cheque.id),
                'text': cls.__get_answer_string_when_add_cheque(fns_cheque),
            }
            Telegram.send_message(new_message)

            cls.__send_message_include_offer_with_best_recomended_price_v2(company, chat_id, fns_cheque)
        return True

    @classmethod
    def process_message(cls, company, chat_id, message):
        if message.find('/cscat') >= 0 or message.find('Cscat') >= 0:
            p = message.split('_')
            if len(p) == 3:
                FNSCheque.change_showcases_category(company, p[1], p[2])
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Категория изменена',
                }
            elif len(p) == 2:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Вы можете указать одну из следующих категорий:\n' + '\n'.join(map(lambda i: i.telegram_emoji + ' ' + i.title + ' /cscat_' + p[1] + '_' + str(i.id), ShowcasesCategory.objects.all()))
                }
            else:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Не веный формат для смены категории',
                }
            Telegram.send_message(new_message)


        #FYI: Отправьте /help чтобы получить справку.
        #И снова здравствуйте! Отправьте /help чтобы получить справку.
        #elif message.find('/help') >= 0 or message.find('Help') >= 0 or message.find('HELP') >= 0 or message.find('help') >= 0:
        elif message.find('/help') >= 0 or message.find('Help') >= 0 or message.find('HELP') >= 0 or message.find('help') >= 0 or \
            message.find('/start') >= 0 or message.find('Start') >= 0 or message.find('START') >= 0 or message.find('start') >= 0:
            new_message = {
                'chat_id': chat_id,
                'text': u"""Help : Здравствуйте, я могу рассказать вам как можно сэкономить при ежедневных походах в магазин.
А также помогу проверить чеки пробитые в магазинах.
Все команды вводятся без кавычек "".
Вы может отправить фото чек с QR кодом и система сама попробует распознать данный чек.
Если фото не четкое попробуйте или заново отсканировать или ввести данные вручную.
Чтобы загрузить чек отправьте, распознанный QR код и укажите вначале /qrcode - пример:
"/qrcode t=20200524T125600&s=849.33&fn=9285000100127361&i=115180&fp=1513716805&n=1"
или просто текст QR кода:
"t=20200524T125600&s=849.33&fn=9285000100127361&i=115180&fp=1513716805&n=1"
или указать следующие данные из чека: ФН, ФД, ФП, сумма с копейками, дату и время продажи.

"/list_nice_categories_X" или "/list_nice_categories_K_L" где X, K, L - ид категорий в данной группе.
"/list_nice" список всех покупок
"/list_by_month" статистика покупок по месяцам в разрезе категорий
Если у вас возникли вопросы, ведите команду /question и ваш вопрос
"/question Добрый день, подскажите как добавить новый элемент?"
Для удаления чека введите команду "/delete_cheque_XXX" где XXX - ид чека.
Чтобы внести новое приобретение введите "/spent; 99.00; БигМак; Макдональдс Москва Большая Бронная ул., 29; 2020-12-12 18:50" 
Таким образом вы укажите через разделитель ";" стоимость покупки, саму покупку, где покупали и когда.
                """
#Чтобы узнать что сегодня следует купить отправьте
#"/basket_today"
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

        elif QRCodeReader.has_5_params_for_create_cheque(message):
            params = QRCodeReader.parse_1(message)
            qr_text = '&'.join(map(lambda k: k + '=' + params[k], params.keys()))
            qr_text += '&n=1'
	    Telegram.__add_new_cheque_by_qr_text_and_send_answer_to_telegram_chat(company, qr_text, chat_id)

        elif message.find('/basket_today') >= 0 or message.find('Basket_today') >= 0:
	    new_message = {
		u'chat_id': chat_id,
		u'text': {
#		    u'Рекомендуем к покупке сегодня': new_recomendate,
#		    u'Среднее потребеление в день': average_weight_per_day,
		},
	    }
	    Telegram.send_message(new_message)
        elif message.find('/list_by_month') >= 0 or message.find('List_by_month') >= 0:
            cheques = {}
            def __get_year_month(date_time):
                #print '----'
                #print date_time
                d = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S').date()
                #print d
                return str(d.year) + '.' + ('0' if d.month <10 else '') + str(d.month)

            ##for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime').values():
            #for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime'):
            #    #TODO нужно работать и с ручными чеками тоже 
            #    if cheque.is_manual:
            #        print 'Alert: Need fix'
            #        continue
            #    print cheque
            #    year_month = __get_year_month(cheque.fns_dateTime)
            #    if not cheques.has_key(year_month):
            #        cheques[year_month] = 0 
            #    cheques[year_month] += int(cheque.fns_totalSum)
            #l = map(lambda x : x + ': ' + str(cheques[x]), sorted(cheques.keys()) )
            #t = '\r\n'.join(l)

            def __get_cat_title(cheque):
                if cheque.showcases_category:
                    return cheque.showcases_category.telegram_emoji + ' ' + cheque.showcases_category.title
                return u'\u2754 Другое'

            d = {}
            for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime','showcases_category'):
                #TODO нужно работать и с ручными чеками тоже 
                if cheque.is_manual:
                    print 'Alert: Need fix'
                    continue

                try:
                    year_month = __get_year_month(cheque.fns_dateTime)
                except:
                    print 'Error: Bad year_month in date!'
                    capture_message('Error: Bad year_month in date!','fatal')
                    year_month = ''
                category_title = __get_cat_title(cheque)

                if not d.has_key(year_month):
                    d[year_month] = {}
                if not d[year_month].has_key(category_title):
                    d[year_month][category_title] = []

                d[year_month][category_title].append(cheque)

            responce = []
            for k in sorted(d.keys()):
                responce.append(u'\U0001f5d3 ' + k)
                for l in sorted(d[k].keys()):
                    total_sum = 0
                    for cheque in  d[k][l]:
                        total_sum += float(cheque.fns_totalSum)
                    #responce.append(' '  + str(float(int(total_sum))/100) + u' \u20bd ' + l)
                    responce.append(l + ': ' + str(float(int(total_sum))/100) + u' \u20bd')
                responce.append(u'\r')

	    new_message = {
		u'chat_id': chat_id,
		u'text': u'\r\n'.join(responce),
	    }
	    Telegram.send_message(new_message)

            #cheques = []
            #current_year_month = ''
            #current_category_title = None
            #current_sum = 0

            #for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime','showcases_category'):
            #    #TODO нужно работать и с ручными чеками тоже 
            #    if cheque.is_manual:
            #        print 'Alert: Need fix'
            #        continue

            #    #print cheque
            #    year_month = __get_year_month(cheque.fns_dateTime)

            #    if current_year_month != year_month:
            #        if current_sum:
            #            cheques.append('  ' + str(float(int(current_sum))/100))
            #        current_sum = 0

            #        current_category_title = None

            #        cheques.append(u'\r')
            #        cheques.append(year_month)
            #        if current_category_title != __get_cat_title(cheque):
            #            cheques.append(' ' + __get_cat_title(cheque))

            #    else:
            #        if current_category_title != __get_cat_title(cheque):

            #            if current_sum:
            #                cheques.append('  ' + str(float(int(current_sum))/100))
            #            current_sum = 0

            #            cheques.append(' ' + __get_cat_title(cheque))
            #    
            #    current_year_month = year_month
            #    #current_category_title = cheque.showcases_category.title if cheque.showcases_category else None
            #    current_category_title = __get_cat_title(cheque)

            #    current_sum += float(cheque.fns_totalSum)
            #        
            #    #if current_year_month != year_month:
            #    #    if current_sum:
            #    #        cheques.append('  ' + str(current_sum))

            #    #    cheques.append(u'\r')
            #    #    cheques.append(year_month)
            #    #    current_year_month = year_month
            #    #    current_category_title = None
            #    #    current_sum = 0
            #    #if cheque.showcases_category and current_category_title != cheque.showcases_category.title:
            #    #    if current_sum:
            #    #        cheques.append('  ' + str(current_sum))
            #    #    cheques.append(' ' + cheque.showcases_category.title)
            #    #    current_category_title = cheque.showcases_category.title
            #    #    current_sum = 0

            #    #current_sum += float(cheque.fns_totalSum)

            #cheques.append('  ' + str(float(int(current_sum))/100))

	    #new_message = {
	    #    u'chat_id': chat_id,
	    #    u'text': u'\r\n'.join(cheques),
	    #}
	    #Telegram.send_message(new_message)
        elif message.find('/list_nice_categories_') >= 0 or message.find('List_nice_categories_') >= 0:
            ms = message.split('_')
            category_ids = ms[3:]
            if ShowcasesCategory.objects.filter(id__in=category_ids).count() != len(category_ids):
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Провеврь коректность указанных категорий, нашили только часть из %s' % (len(category_ids)),
                }
                Telegram.send_message(new_message)
                return 
            else:
                showcases_categories = ShowcasesCategory.objects.filter(id__in=category_ids)
                

            cheques = FNSCheque.objects.filter(company=company, showcases_category__in=showcases_categories).order_by('fns_dateTime','showcases_category')
            #for cheque in FNSCheque.objects.filter(company=company, showcases_category__in=showcases_categories).order_by('fns_dateTime','showcases_category'):

            cls.__send_many_prepared_message(chat_id, cheques)

        elif message.find('/list_nice') >= 0 or message.find('List_nice') >= 0:
            cheques = FNSCheque.objects.filter(company=company).order_by('fns_dateTime','showcases_category')
            #for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime','showcases_category'):

            cls.__send_many_prepared_message(chat_id, cheques)

            #def __get_year_month_day(date_time):
            #    #print '----'
            #    #print date_time
            #    d = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S').date()
            #    #print d
            #    #return str(d.year) + '.' + ('0' if d.month <10 else '') + str(d.month) + '.' + ('0' if d.day <10 else '') + str(d.day)
            #    return ('0' if d.day <10 else '') + str(d.day) + '.' + ('0' if d.month <10 else '') + str(d.month) + '.' + str(d.year) 

            #cheques = []
            #current_date = ''
            #current_category_title = ''
            #for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime','showcases_category'):
            #    if cheque.is_manual:
            #        print 'Alert: Need fix'
            #        continue
            #    #cheques.append(__get_year_month_day(cheque.fns_dateTime) + ' ' + cheque.get_shop_short_info_string() + ' ' + str(cheque.fns_totalSum))
            #    date = __get_year_month_day(cheque.fns_dateTime)
            #    if current_date != date:
            #        cheques.append('\r')
            #        cheques.append(date)
            #        current_date = date
            #        current_category_title = ''
            #    if cheque.showcases_category:
            #        showcases_category_str = cheque.showcases_category.telegram_emoji + ' ' + cheque.showcases_category.title
            #    if cheque.showcases_category and current_category_title != showcases_category_str:
            #        cheques.append(showcases_category_str)
            #        current_category_title = showcases_category_str
            #    cheques.append(' ' + str(float(cheque.fns_totalSum) / 100) + u' \u20bd - ' + cheque.get_shop_short_info_string() + ' /cheque_' + str(cheque.id))
            ##cheques.append(u'Всего покупок: ' + str(len(cheques)))
	    #new_message = {
	    #    u'chat_id': chat_id,
	    #    u'text': '\r\n'.join(cheques),
	    #}
	    #Telegram.send_message(new_message)
        elif message.find('/list') >= 0 or message.find('List') >= 0:
            cheques = []
            for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime'):
                cheques.append({
                    u'totalSum': str(cheque.fns_totalSum) + u' \u20bd',
                    #u'see': u'/cheque ' + str(cheque.id),
                    u'see': u'/cheque_' + str(cheque.id),
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
            elif message.find('/cheque_') >= 0 or message.find('Cheque_') >= 0:
                request = message.split('_')
                if len(request) > 1:
                    cheque_id = request[1]
            else:
                cheque_id = message[7:]
            if not cheque_id:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: не нашли чек с таким id = ' + cheque_id
                }
                Telegram.send_message(new_message)
                return

	    cheque_ids = re.findall(u'^(\d+)$', cheque_id)
            if len(cheque_ids) != 1:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: не нашли чек с таким id = ' + cheque_id
                }
                Telegram.send_message(new_message)
                return
            cheque_id = cheque_ids[0]

            cheques = FNSCheque.objects.filter(company=company, id=cheque_id)
            if len(cheques) > 1:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: нащли больше чем 1 чек с таким id = ' + cheque_id
                }
                Telegram.send_message(new_message)
            elif len(cheques) < 1:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: не нашли чек с таким id = ' + cheque_id
                }
                Telegram.send_message(new_message)
            elif len(cheques) == 1:
                cheque = cheques[0]
                elements = []
                element_strs = []
                for e in FNSChequeElement.objects.filter(fns_cheque=cheque):
                    elements.append([e.get_title(), str(e.get_price()), str(e.get_quantity()), str(e.get_sum())])
                    element_strs.append(' ' + e.get_title() + ' ' + str(float(int(e.get_price())) / 100) + u' \u20bd ' + str(e.get_quantity()) + ' ш. ' + str(float(int(e.get_sum())) / 100) + u' \u20bd') 
                if cheque.is_manual:
                    elements.append(cheque.manual_what)


                recomended_showcases_category = cheque.get_recomended_showcases_category()
                new_message = {
                    u'chat_id': chat_id,
                    #u'text': {
                    #    u'Общая сумма': cheque.fns_totalSum,
                    #    u'Дата покупки': cheque.fns_dateTime,
                    #    u'Всего позиций в чек': str(len(elements)),
                    #    u'Ваши покупки': elements,
                    #    u'Приобретено в': cheque.get_address(),
                    #    u'Для удаения чека пройдите по ссылке': '/delete_cheque_' + str(cheque.id),
                    #},
                    u'text': u'Общая сумма: ' + str(float(cheque.fns_totalSum) / 100) + u' \u20bd\n' + 
                        u'Дата покупки: ' + str(cheque.fns_dateTime) + '\n' + 
                        ((u'Категория магазина: ' + cheque.showcases_category.telegram_emoji + ' ' + cheque.showcases_category.title + '\n') if cheque.showcases_category else ('Если хотите установить категорию "' + recomended_showcases_category.telegram_emoji + ' ' + recomended_showcases_category.title + '" отправьте команду /cscat_' + str(cheque.id) + '_' + str(recomended_showcases_category.id) + '\n')) + 
                        u'Приобретено в: ' + cheque.get_shop_short_info_string() + '\n' + 
                        u'Всего позиций в чек: ' + str(len(elements)) + '\n' + 
                        u'Ваши покупки:\r\n' +  '\r\n'.join(element_strs) + '\n' + 
                        u'Для удаления чека пройдите по ссылке: ' + '/delete_cheque_' + str(cheque.id) + '\n' +
                        u'Для перехода в режим изменения категории введите команду /cscats_' + str(cheque.id),
                }
	        Telegram.send_message(new_message)
            else:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: не известная ошибка',
                }
                Telegram.send_message(new_message)

            cls.__send_message_include_offer_with_best_recomended_price_v2(company, chat_id, cheque)
               
        elif message.find('/delete_cheque') >= 0 or message.find('Delete_cheque') >= 0:
            request = message.split(' ')
            if len(request) > 1:
                cheque_id = request[1]
            elif message.find('/delete_cheque_') >= 0 or message.find('Delete_cheque_') >= 0:
                request = message.split('_')
                if len(request) > 2:
                    cheque_id = request[2]
            else:
                cheque_id = message[14:]

            if not cheque_id:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: не нашли чек с таким id = ' + cheque_id
                }
                Telegram.send_message(new_message)
                return

            cheques = FNSCheque.objects.filter(company=company, id=cheque_id)
            if len(cheques) > 1:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: нащли больше чем 1 чек с таким id = ' + cheque_id
                }
                Telegram.send_message(new_message)
            elif len(cheques) < 1:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: не нашли чек с таким id = ' + cheque_id
                }
                Telegram.send_message(new_message)
            elif len(cheques) == 1:
                cheque = cheques[0]
                cheque_id = cheque.id
                cheque.delete()
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Чек с id = ' + str(cheque_id) + ' успешно удален.',
                }
	        Telegram.send_message(new_message)
            else:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: не известная ошибка',
                }
                Telegram.send_message(new_message)

        elif message.find('/spent') >= 0 or message.find('Spent') >= 0 or message.find('spent') >= 0 or \
            message.find('/spend') >= 0 or message.find('Spend') >= 0 or message.find('spend') >= 0: 

            p = message.split(';')
            if len(p) == 4:
                now = datetime.now()
                p.append(now.strftime('%Y-%m-%dT%H:%M'))
            cheque = FNSCheque.create_and_save_cheque_from_text(company, p[1], p[2], p[3], p[4])
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Ваш чек от ' + str(cheque.get_datetime()) + u' на сумму ' + cheque.fns_totalSum + u' \u20bd приобретенный в "' + cheque.manual_where  + '" сохранен. Расширенная информация по чеку доступна по команде /cheque_' + str(cheque.id)
            }
            Telegram.send_message(new_message)

    @classmethod
    def __send_error_when_load_photo_with_qr_kode(cls, chat_id, fns_cheque_json):
        print 'Error: ...'
        print fns_cheque_json
        new_message = {
            'chat_id': chat_id,
            'text': fns_cheque_json
        }
        Telegram.send_message(new_message)
        new_message = {
            'chat_id': chat_id,
            'text': u'Ошибка сервера! Просим вас, отправить данное сообщение в нашу службу поддержке. Этим вы очень поможет быстрее решить проблему.',
        }
        Telegram.send_message(new_message)
        new_message = {
            'chat_id': chat_id,
            'text': u'Возможно на чеке есть дургой QR код? Бывает продавец печатает несколько QR кодов. \nТакже вы можете попробовать сделать более четкую фотографию чека и QR кода на нем, или ввести данные из чека ("ФП", "ФН", "ФД", сумму в рублях с копейками, дату и время. Указав параметры как написано в /help).',
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
        #except:
	except Exception as e:
            import traceback
            traceback.print_exc()

	    capture_exception(e)

        #responce = urllib2.urlopen(request, timeout=request_timeout)
#	print "result code: " + str(responce.getcode()) 
#	#data = weburl.read()
#	#print data
#	data_r = json.load(responce)
#	print data_r

    @classmethod
    def __send_many_prepared_message(cls, chat_id, cheques):
        d = {}
        for cheque in cheques:
            #TODO нужно работать и с ручными чеками тоже 
            if cheque.is_manual:
                print 'Alert: Need fix'
                continue

            year_month_day = cls.__get_year_month_day(cheque.fns_dateTime)
            category_title = cls.__get_cat_title(cheque)

            if not d.has_key(year_month_day):
                d[year_month_day] = {}
            if not d[year_month_day].has_key(category_title):
                d[year_month_day][category_title] = []

            d[year_month_day][category_title].append(cheque)

        responces = []
        count = 0
        max_count_in_one_message = 20
        responce = []
        for k in sorted(d.keys()):
            date = k
            responce.append(u'\U0001f5d3 ' + str(date.day) + '.' + str(date.month) + '.' + str(date.year))
            for l in sorted(d[k].keys()):
                responce.append('' + l + ':')
                for cheque in d[k][l]:
                    responce.append('  ' + str(float(cheque.fns_totalSum) / 100) + u' \u20bd {' + cheque.get_shop_short_info_string() + '} /cheque_' + str(cheque.id))
                    count += 1
                    if count > max_count_in_one_message:
                        responces.append(responce)
                        print '++++'
                        print responces
                        responce = []
                        print responces
                        print '===='
                        count = 0


            responce.append(u'\r')
        responces.append(responce)

        for responce in responces:
            new_message = {
                u'chat_id': chat_id,
                u'text': u'\r\n'.join(responce),
            }
            Telegram.send_message(new_message)
	    time.sleep(3)

    @classmethod
    def __send_message_include_offer_with_best_recomended_price(cls, chat_id, cheque):
        element_2_elements = {}
        for element in FNSChequeElement.objects.filter(fns_cheque=cheque):
            title = element.name
            element_2_elements[element] = []
            result_strings = element.list_string_for_search()
            for result_string in result_strings:
                for e in FNSChequeElement.objects.filter(name__contains=result_string[1]).exclude(sum=0): #TODO не хватет посика по расстоянию(местам) и времени доспности предложения
                    element_2_elements[element].append(e)
        summ = cls.__calc_sum_for_cheque_with_new_offer(cheque, element_2_elements)
        dpt = cls.__difference_percent_total(cheque, summ)
        if int(dpt[1]) > 3 or int(dpt[0]) > 50 or True:
            new_message = {
                u'chat_id': chat_id,
                u'text': str(int(dpt[0])) + u' стольво вы могли сберечь, это ' + str(dpt[1]) + u'% от уплаченной суммы ' + str(dpt[2]),
            }
            Telegram.send_message(new_message)
            summ = 0
            r = []
            for k in element_2_elements.keys():
                if not len(element_2_elements[k]):
                    print '!!!!!!!!! error'
                    continue
                #TODO пока работаем только с теми товарами которые идут в штуках и не имют веса - кофты курки.
                # Еще есть товары весовые и товары е весове но у которых не не проставили или не смоглди автоматом определить вес.
                # Если торвары разные а цена у предоженного ниже то выводим.
                r.append(cls.__transfer_from_cheque_element_to_message_text('00) -', k))
                if k.is_element_piece():
                    element_2_elements[k].sort(key = lambda o : o.get_price())
                    r.append(cls.__transfer_from_cheque_element_to_message_text('10) +', element_2_elements[k][0]))
                elif k.has_weight():
                    has_weight = []
                    has_not_weight = []
                    for o in element_2_elements[k]:
                        if o.get_price_per_one_gram():
                            has_weight.append(o)
                        else:
                            has_not_weight.append(o)
                    has_weight.sort(key = lambda o : o.get_price_per_one_gram())
                    has_not_weight.sort(key = lambda o : o.get_price())
                    if len(has_weight):
                        r.append(cls.__transfer_from_cheque_element_to_message_text('21) +', has_weight[0]))
                    if len(has_not_weight):
                        r.append(cls.__transfer_from_cheque_element_to_message_text('21) ?', has_not_weight[0]))
                else:
                    has_weight = []
                    has_not_weight = []
                    for o in element_2_elements[k]:
                        if o.get_price_per_one_gram():
                            has_weight.append(o)
                        else:
                            has_not_weight.append(o)
                    has_weight.sort(key = lambda o : o.get_price_per_one_gram())
                    has_not_weight.sort(key = lambda o : o.get_price())
                    if len(has_weight):
                        r.append(cls.__transfer_from_cheque_element_to_message_text('31) +', has_weight[0]))
                    if len(has_not_weight):
                        r.append(cls.__transfer_from_cheque_element_to_message_text('31) ?', has_not_weight[0]))
                element_2_elements[k].sort(key = lambda o : o.get_price())
                r.append(cls.__transfer_from_cheque_element_to_message_text('40) +', element_2_elements[k][0]))
                for e in element_2_elements[k]:
                    if k.get_price() / 5 <= e.get_price() <= k.get_price():
                        r.append(cls.__transfer_from_cheque_element_to_message_text('50) +', element_2_elements[k][0]))
                        summ += k.get_quantity() * e.get_price()
                        break
                else:
                    summ += k.get_quantity() * k.get_price()
            dpt = cls.__difference_percent_total(cheque, summ/100)
            new_message = {
                u'chat_id': chat_id,
                u'text': str(int(dpt[0])) + u' стольво вы моголи сберечь, это ' + str(dpt[1]) + u'% от уплаченной суммы ' + str(dpt[2]),
            }
            Telegram.send_message(new_message)
            if not r:
                return
            new_message = {
                u'chat_id': chat_id,
                'text': '\n'.join(r),
            }
            Telegram.send_message(new_message)

    @classmethod
    def __send_message_include_offer_with_best_recomended_price_v2(cls, company, chat_id, cheque):
        # нужно пока остановить рекомнедации так как отжирает много памяти и падает
        return

        element_2_elements = {}
        for element in FNSChequeElement.objects.filter(fns_cheque=cheque):
            title = element.name
            element_2_elements[element] = []
            result_strings = element.list_string_for_search()
            for result_string in result_strings:
                for e in FNSChequeElement.objects.filter(name__contains=result_string[1]).exclude(sum=0): #TODO не хватет посика по расстоянию(местам) и времени доспности предложения
                    element_2_elements[element].append(e)

        city_title = FNSCheque.current_city_title(company)

        element_2_best_element = {}
        summ = 0
        for k in element_2_elements.keys():
            if not len(element_2_elements[k]):
                print '!!!!!!!!! error'
                continue
            #TODO пока работаем только с теми товарами которые идут в штуках и не имют веса - кофты курки.
            # Еще есть товары весовые и товары е весове но у которых не не проставили или не смоглди автоматом определить вес.
            # Если торвары разные а цена у предоженного ниже то выводим.

            #element_2_elements[k].sort(key = lambda o : o.get_price())
            #for e in element_2_elements[k]:
            #    if k.get_price() / 5 <= e.get_price() < k.get_price():
            #        element_2_best_element[k] = e
            #        summ += k.get_quantity() * e.get_price()
            #        break
            #else:
            #    summ += k.get_quantity() * k.get_price()


            #сначала сгруппируем по магазинам и удалим для одного товара данные за несколько покупок
            shop_2_elements = {}
            for i in element_2_elements[k]:
                uniq_key = i.fns_cheque.get_shop_info_string() + i.get_title()
                if not shop_2_elements.get(uniq_key):
                    shop_2_elements[uniq_key]= []
                shop_2_elements[uniq_key].append(i)

            elements = []
            for h in shop_2_elements.keys():
	        #if not re.findall(u'осква', h):
                #    continue
                #print 'god h =', h.encode('utf8')
                #for city_title in FNSCheque.current_city_title(company):
                if not re.findall(city_title, h):
                    continue

                shop_2_elements[h].sort(key = lambda o : o.get_datetime())
                elements.append(shop_2_elements[h][-1])

            elements.sort(key = lambda o : o.get_price())
            for e in elements:
                if k.get_price() / 5 <= e.get_price() < k.get_price():
                    element_2_best_element[k] = e
                    summ += k.get_quantity() * e.get_price()
                    break
            else:
                summ += k.get_quantity() * k.get_price()
        dpt = cls.__difference_percent_total(cheque, summ/100)
        if int(dpt[1]) > 3 or int(dpt[0]) > 50:
            pass
        else:
            return

        new_message = {
            u'chat_id': chat_id,
            u'text': str(int(dpt[0])) + u' руб. столько вы моголи сберечь, это ' + str(dpt[1]) + u'% от уплаченной суммы ' + str(dpt[2]),
        }
        Telegram.send_message(new_message)

        #rr = []
        #r = []
        #count = 0
        #max_count = 15
        #for k in element_2_best_element.keys():
        #    r.append(cls.__transfer_from_cheque_element_to_message_text_v1('-', k))
        #    r.append(cls.__transfer_from_cheque_element_to_message_text_v1('+', element_2_best_element[k]))
        #    count += 1
        #    if count > max_count:
        #        rr.append(r)
        #        r = []
        #        count = 0
        #rr.append(r)
        #if not rr:
        #    return
        #for r in rr:
        #    new_message = {
        #        u'chat_id': chat_id,
        #        'text': '\n'.join(r),
        #    }
        #    Telegram.send_message(new_message)
        
        #element_2_shop_2_best_element = {}
        #for k in element_2_elements.keys():
        #    if not len(element_2_elements[k]):
        #        print '!!!!!!!!! error'
        #        continue
        #    #TODO пока работаем только с теми товарами которые идут в штуках и не имют веса - кофты курки.
        #    # Еще есть товары весовые и товары е весове но у которых не не проставили или не смоглди автоматом определить вес.
        #    # Если торвары разные а цена у предоженного ниже то выводим.
        #    element_2_elements[k].sort(key = lambda o : o.get_price())
        #    for e in element_2_elements[k]:
        #        if not element_2_shop_2_best_element.get(k):
        #            element_2_shop_2_best_element[k] = {}
        #        if not element_2_shop_2_best_element[k].get(e.get_shop_info_string()):
        #            element_2_shop_2_best_element[k][e.get_shop_info_string()] = []
        #        element_2_shop_2_best_element[k][e.get_shop_info_string()].append(e)
        #    else:
        #        summ += k.get_quantity() * k.get_price()
        #dpt = cls.__difference_percent_total(cheque, summ/100)
 
        #get_shop_info_string()

        shop_2_element_2_best_element = {}
        for k in element_2_best_element.keys():
            if not shop_2_element_2_best_element.get(element_2_best_element[k].fns_cheque.get_shop_info_string()):
                shop_2_element_2_best_element[element_2_best_element[k].fns_cheque.get_shop_info_string()] = {}
            #if not shop_2_element_2_best_element[e.get_shop_info_string()].get(k):
            #    shop_2_element_2_best_element[e.get_shop_info_string()][k] = []
            #shop_2_element_2_best_element[e.get_shop_info_string][k].append(e)
            shop_2_element_2_best_element[element_2_best_element[k].fns_cheque.get_shop_info_string()][k] = element_2_best_element[k]

        rr = []
        r = []
        count = 0
        max_count = 15
        for shop in shop_2_element_2_best_element.keys():
            r.append(u'\U0001f3db' + shop)
            for k in shop_2_element_2_best_element[shop]:
                #r.append(cls.__transfer_from_cheque_element_to_message_text_v2('-', k))
                r.append(cls.__transfer_from_cheque_element_to_message_text_v2(u'\u2796', k))
                #r.append(cls.__transfer_from_cheque_element_to_message_text_v2('+', shop_2_element_2_best_element[shop][k]))
                r.append(cls.__transfer_from_cheque_element_to_message_text_v3(u'\u2795', shop_2_element_2_best_element[shop][k]))
                count += 1
                if count > max_count:
                    rr.append(r)
                    r = []
                    count = 0
        rr.append(r)
        if not rr:
            return
        for r in rr:
            new_message = {
                u'chat_id': chat_id,
                'text': '\n'.join(r),
            }
            Telegram.send_message(new_message)

    def __send_prepared_message(cls, chat_id, cheques):
        d = {}
        for cheque in cheques:
            #TODO нужно работать и с ручными чеками тоже 
            if cheque.is_manual:
                print 'Alert: Need fix'
                continue

            year_month_day = cls.__get_year_month_day(cheque.fns_dateTime)
            category_title = cls.__get_cat_title(cheque)

            if not d.has_key(year_month_day):
                d[year_month_day] = {}
            if not d[year_month_day].has_key(category_title):
                d[year_month_day][category_title] = []

            d[year_month_day][category_title].append(cheque)

        responce = []
        for k in sorted(d.keys()):
            date = k
            responce.append(u'\U0001f5d3 ' + str(date.day) + '.' + str(date.month) + '.' + str(date.year))
            for l in sorted(d[k].keys()):
                responce.append('' + l + ':')
                for cheque in d[k][l]:
                    responce.append('  ' + str(float(cheque.fns_totalSum) / 100) + u' \u20bd {' + cheque.get_shop_short_info_string() + '} /cheque_' + str(cheque.id))
            responce.append(u'\r')
        new_message = {
            u'chat_id': chat_id,
            u'text': u'\r\n'.join(responce),
        }
        Telegram.send_message(new_message)

    @classmethod
    def __transfer_from_cheque_element_to_message_text(cls, sufix, e):
        k = e
        return sufix + ' all price_KG: ' + (str(k.get_price_per_one_gram() / 100 * float(k.get_quantity()) * k.get_weight()) if k.get_price_per_one_gram() else '*') + ' R. one_KG: ' + (str(k.get_price_per_one_gram() / 100) if  k.get_price_per_one_gram() else '*') + ' R. price: ' + str(k.get_price() / 100) + ' R. sum: ' +  str(k.get_sum() / 100) + ' R. ' + ' qty: ' +str( k.get_quantity()) + ' title: ' + k.get_title()

    @classmethod
    def __transfer_from_cheque_element_to_message_text_v1(cls, sufix, k):
        #return sufix + ' ' + str(k.get_price() / 100) + ' руб. ' + k.get_title() + ' ' + k.fns_cheque.get_shop_short_info_string() + ' ' + k.fns_cheque.get_datetime()
        return sufix + ' ' + str(k.get_price() / 100) + ' руб. ' + k.get_title() + ' -> ' + k.fns_cheque.get_shop_short_info_string()

    @classmethod
    def __transfer_from_cheque_element_to_message_text_v2(cls, sufix, k):
        return sufix + ' ' + str(k.get_price() / 100) + u' \u20bd ' + k.get_title()

    @classmethod
    def __transfer_from_cheque_element_to_message_text_v3(cls, sufix, k):
        last_update_datetime = k.fns_cheque.format_fns_dateTime_2_DateTime()
        t = last_update_datetime.timetuple()
        m = [u'января', u'февраля', u'марта', u'апреля', u'мая', u'июня', u'июля', u'августа', u'сентября', u'октября', u'ноября', u'декабря']
        #return sufix + ' ' + str(k.get_price() / 100) + u' \u20bd ' + k.get_title() + ' ' + k.get_datetime() + u' обновление от ' + m[t[1]-1] + ' ' + str(t[0])
        return sufix + ' ' + str(k.get_price() / 100) + u' \u20bd ' + k.get_title() + u' обновление от ' + m[t[1]-1] + ' ' + str(t[0])

    @classmethod
    def __was_message_processed(cls, update_id):
        if ProcessedMessage.objects.filter(update_id=update_id):
            return True
        return False
