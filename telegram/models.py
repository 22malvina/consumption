# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from cheque.models import QRCodeReader, FNSCheque, ImportProverkachekaComFormatLikeFNS, FNSChequeElement
import json
import urllib
import urllib2
#import  base64
from django.conf import settings
from company.models import Employee, Company

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


#https://api.telegram.org/bot1185379535:AAFH80I6a84DA26U1ue91IOj3o5TpyfOZx0/getFile?file_id=AgACAgIAAxkBAAIOLV_bm_ADUaQ8SPjcyA1Ht44OVxQsAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ
#{
#    "ok": true,
#    "result": {
#        "file_id": "AgACAgIAAxkBAAIOMF_boXZYtLpffoHzg47fU0v06wNUAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ",
#        "file_unique_id": "AQADmo2gli4AAz5sBQAB",
#        "file_size": 85969,
#        "file_path": "photos/file_1.jpg"
#    }
#}

#https://api.telegram.org/file/bot1185379535:AAFH80I6a84DA26U1ue91IOj3o5TpyfOZx0/photos/file_1.jpg
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
    def __add_new_cheque_by_qr_text_and_send_answer_to_telegram_chat(cls, company, qr_text, chat_id):
        if not FNSCheque.is_it_qr_test(qr_text):
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Данных параметров не достаточно для проверки чека.',
            }
            Telegram.send_message(new_message)
            return

        if FNSCheque.has_cheque_with_qr_text(company, qr_text):
            cheque = FNSCheque.get_cheque_with_qr_text(company, qr_text)
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Такой чек уже существует в данном чате! /cheque' + str(cheque.id),
            }
            Telegram.send_message(new_message)
            return
        else:
            fns_cheque = FNSCheque.create_save_update_fns_cheque_from_proverkacheka_com(qr_text, company)

        if fns_cheque:
            fns_cheque = FNSCheque.objects.get(id=fns_cheque.id)

            new_message = {
                'chat_id': chat_id,
                'text': u'Здесь будет в JSON чека полученный от ФНС',
            }
            Telegram.send_message(new_message)
            new_message = {
                u'chat_id': chat_id,
                #u'text': u'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' руб. сохранен.'
                'text': cls.__get_answer_string_when_add_cheque(fns_cheque),
            }
            Telegram.send_message(new_message)
        else:
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Не смогли загрузить ваш чек :' + qr_text,
            }
            Telegram.send_message(new_message)
 
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
        return 'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' руб. приобретенный в ' + fns_cheque.get_shop_info_string() + ' сохранен. Расширенная информация по чеку доступна по команде /cheque' + str(fns_cheque.id)

    @classmethod
    def get_fns_cheque_json_from_proverkacheka_com(cls, new_file):
        #работает
        #curl -F 'qrfile=@AgACAgIAAxkBAAIOLV_bm_ADUaQ8SPjcyA1Ht44OVxQsAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ'  https://proverkacheka.com/check/get

        import requests
        #так работает
        #with open('AgACAgIAAxkBAAIOLV_bm_ADUaQ8SPjcyA1Ht44OVxQsAAKbsjEboo7ZSqgpZRT7PU4omo2gli4AAwEAAwIAA3kAAz5sBQABHgQ', 'rb') as f:
        #    r = requests.post('https://proverkacheka.com/check/get', files={'qrfile': f})



        r = requests.post('https://proverkacheka.com/check/get', files={'qrfile': new_file})

        #print r.text.encode('utf8')
        #rr = r.json()
        #print r.headers['Content-Type']
        #print r.status_code
        #print r.raise_for_status()  
        if r.status_code == requests.codes.ok:
            decoded_result = r.json()
            return decoded_result
        else:
            print r.text.encode('utf8')
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
    def process_file(cls, company, chat_id, file_id):

        file_info = cls.get_file_info(file_id)
        file_path = file_info['file_path']

        new_file = cls.get_file(file_path)

        f = open(file_id, "a")
        f.write(new_file)
        f.close()
        #пока не сохраняем сразу отправляем дальше в проверку чеков

        fns_cheque_json = cls.get_fns_cheque_json_from_proverkacheka_com(new_file)
        if not fns_cheque_json:
            return False

        #print fns_cheque_json
        fns_cheque_json["document"] = {}
        fns_cheque_json["document"]["receipt"] = fns_cheque_json['data']['json']

        if FNSCheque.has_cheque_with_fns_cheque_json(company, fns_cheque_json):
            cheque = FNSCheque.get_cheque_with_fns_cheque_json(company, fns_cheque_json)
            new_message = {
                u'chat_id': chat_id,
                u'text': u'Такой чек уже существует в данном чате! /cheque' + str(cheque.id),
            }
            Telegram.send_message(new_message)
            return False

        fns_cheque = FNSCheque(company=company)
        #TODO проверить что такого чека еще нет в этой окмпании а то получается 2 раза один и тот же чек добавить
        fns_cheque.save()

        #FNSCheque.update_cheque_from_json(fns_cheque, fns_cheque_json)
        fns_cheque.update_cheque_from_json(fns_cheque_json)

        if fns_cheque:
            fns_cheque = FNSCheque.objects.get(id=fns_cheque.id)

            new_message = {
                'chat_id': chat_id,
                'text': u'Здесь будет в JSON чека полученный от ФНС',
            }
            Telegram.send_message(new_message)
            new_message = {
                u'chat_id': chat_id,
                #u'text': u'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' руб. приобретенный в ' + fns_cheque.get_user() + ' ' + fns_cheque.get_user_inn() + ' ' + fns_cheque.get_address() + ' сохранен. Расширенная информация по чеку доступна по команде /cheque' + str(fns_cheque.id),
                #u'text': u'Ваш чек от ' + fns_cheque.fns_dateTime.replace('T', ' ') + u' на сумму ' + str(float(fns_cheque.fns_totalSum)/100) + u' руб. приобретенный в ' + fns_cheque.get_shop_info_string() + ' сохранен. Расширенная информация по чеку доступна по команде /cheque' + str(fns_cheque.id),
                'text': cls.__get_answer_string_when_add_cheque(fns_cheque),
            }
            Telegram.send_message(new_message)
        return True

    @classmethod
    def process_message(cls, company, chat_id, message):
        #FYI: Отправьте /help чтобы получить справку.
        #И снова здравствуйте! Отправьте /help чтобы получить справку.
        if message.find('/help') >= 0 or message.find('Help') >= 0 or message.find('HELP') >= 0 or message.find('help') >= 0:
            new_message = {
                'chat_id': chat_id,
                'text': u"""Help : Здравствуйте, я могу рассказать вам как можно сэкономить при ежедневных походах в магазин.
А также помогу проверить чеки пробитые в магазинах.
Чтобы загрузить чек отправьте, распознанный QR код и укажите вначале /qrcode - пример:
/qrcode t=20200524T125600&s=849.33&fn=9285000100127361&i=115180&fp=1513716805&n=1
или просто текст QR кода:
t=20200524T125600&s=849.33&fn=9285000100127361&i=115180&fp=1513716805&n=1
Чтобы узнать что сегодня следует купить отправьте
/basket_today
/list список всех покупок
Если у вас возникли вопросы, ведите команду /question и ваш вопрос
/question Добрый день, подскажите как добавить новый элемент?
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

        elif QRCodeReader.has_5_params_for_create_cheque(message):
            params = QRCodeReader.parse_1(message)
            qr_text = '&'.join(map(lambda k: k + '=' + params[k], params.keys()))
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
        elif message.find('/list') >= 0 or message.find('List') >= 0:
            cheques = []
            for cheque in FNSCheque.objects.filter(company=company).order_by('fns_dateTime'):
                cheques.append({
                    u'totalSum': str(cheque.fns_totalSum),
                    #u'see': u'/cheque ' + str(cheque.id),
                    u'see': u'/cheque' + str(cheque.id),
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
                for e in FNSChequeElement.objects.filter(fns_cheque=cheque):
                    elements.append([e.get_title(), str(e.get_price()), str(e.get_quantity()), str(e.get_sum())])
                new_message = {
                    u'chat_id': chat_id,
                    u'text': {
                        u'Общая сумма': cheque.fns_totalSum,
                        u'Дата покупки': cheque.fns_dateTime,
                        u'Всего товаров в чек': str(len(elements)),
                        u'Ваши покупки': elements,
                        u'Для удаения чека пройдите по ссылке': '/delete_cheque_' + str(cheque.id),
                    },
                }
	        Telegram.send_message(new_message)
            else:
                new_message = {
                    u'chat_id': chat_id,
                    u'text': u'Error: не известная ошибка',
                }
                Telegram.send_message(new_message)
               
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

    @classmethod
    def __was_message_processed(cls, update_id):
        if ProcessedMessage.objects.filter(update_id=update_id):
            return True
        return False
