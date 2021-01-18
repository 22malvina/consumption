# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from company.models import Company

import time
import json
import urllib
import urllib2, base64

import re

import ast # нужен для того чтобы из сохраненного как бы джисона достать данные

from datetime import datetime

"""
json чека ипортированного из ФНС России
место хранения

t=20200603T145000&s=3390.59&fn=9282440300628259&i=2031&fp=2548611914&n=1

{
    "document": {
        "receipt": {
            "ecashTotalSum":339059,
            "fiscalDriveNumber":"9282440300628259",
            "retailPlaceAddress":"107076, г.Москва, ул.Богородский Вал, д.6, корп.2",
            "fiscalDocumentNumber":2031,
            "taxationType":1,
            "shiftNumber":8,
            "userInn":"5258056945",
            "operationType":1,
            "receiptCode":3,
            "items":[
                {
                    "price":2990,
                    "name":"240 КАРТОФЕЛЬ",
                    "quantity":1.93,
                    "sum":5771
                },
                {"price":5990,"name":"4607045982771 МОЛОКО SPAR УЛЬТРАПА","quantity":3,"sum":17970},
                {"price":5990,"name":"7622210736970 ШОКОЛАД MILKA МОЛОЧН","quantity":1,"sum":5990},
            ],
            "user":"ООО \"Спар Миддл Волга\"",
            "fiscalSign":2548611914,
            "dateTime":"2020-06-03T14:50:00",
            "requestNumber":8,
            "totalSum":339059,
            "nds10":22252,
            "rawData": "",
            "nds18":15718,
            "cashTotalSum":0,
            "kktRegId":"0001732259050091    ",
            "operator":"Усикова Дарья Игорев"
        }
    }
}
"""

class ShowcasesCategory(models.Model):
    """
    Катигории витрин которые реализуют продукцию
    Гипермаркет, Финансовые операции, Кафе и рестораны, Мобильная связь, Общественный транспорт, Одежда и обувь, Отпуск и путешествия, Медицина и аптеки, Красота и здоровье
    """
    title = models.CharField(blank=True, max_length=254)
    telegram_emoji = models.CharField(blank=True, max_length=254)

    def __unicode__(self):
        return u"%s %s" % (self.title, self.telegram_emoji)

class FNSCheque(models.Model):
    json = models.TextField(blank=True, )
    company = models.ForeignKey(Company, blank=True, null=True) #TODO чек простой элемент и компанию надо вынести из чека
    showcases_category = models.ForeignKey(ShowcasesCategory, blank=True, null=True) #TODO чек простой элемент и категорию витрины на которй он был пробит надо убрать

#    datetime_create = models.DateTimeField(blank=True, auto_now_add = True)
    fns_userInn = models.CharField(blank=True, max_length=254) # ИНН организации

    #t=20200523T2158&s=3070.52&fn=9289000100405801&i=69106&fp=3872222871&n=1
    fns_fiscalDocumentNumber = models.CharField(blank=True, max_length=254) #FD i ФД
    fns_fiscalDriveNumber = models.CharField(blank=True, max_length=254) #FN fn ФН
    fns_fiscalSign = models.CharField(blank=True, max_length=254) #FDP fp ФП

    fns_dateTime = models.CharField(blank=True, max_length=254) #date t
    fns_totalSum = models.CharField(blank=True, max_length=254) #sum s

    # ручно режим
    is_manual = models.BooleanField() # если выставлено то значит ручная тарат
    #manual_how_much = models.CharField(blank=True, max_length=254) # используем fns_totalSum
    manual_what = models.CharField(blank=True, max_length=254)
    manual_where = models.CharField(blank=True, max_length=254)
    #manual_when = models.CharField(blank=True, max_length=254) # используем fns_dateTime чтобы сортировать

    @classmethod
    def __cities(cls):
        return [
u'116 –й км.', u'Абаза', u'Абакан', u'Абан', u'Абатское', u'Абдулино', u'Абинск', u'Агидель', u'Агинский', u'Агинское', u'Агрыз', u'Адлер', u'Адыгейск', u'Азнакаево', u'Азов', u'Айхал', u'Академгородок', u'Акбулак', u'Аксай', u'Акъяр', u'Алагир', u'Алапаевск', u'Алатырь', u'Алдан', u'Алейск', u'Александров', u'Александров Гай', u'Александровск', u'Александровское', u'Александровское', u'Алексеевка', u'Алексеевка (Белгородская область)', u'Алексин', u'Алтайское', u'Альметьевск', u'Амга', u'Амурск', u'Анадырь', u'Анапа', u'Анастасиевка', u'Анастасиевская', u'Ангарск', u'Андреаполь', u'Андреевка', u'Анжеро-Судженск', u'Анна', u'Апаринки', u'Апатиты', u'Апрелевка', u'Апшеронск', u'Арамиль', u'Аргаяш', u'Аргун', u'Ардатов', u'Ардон', u'Арзамас', u'Аркадак', u'Армавир', u'Арсеньев', u'Арск', u'Артем', u'Артемовский', u'Арти', u'Архангельск', u'Архара', u'Архипо-Осиповка', u'Архипо-Осиповский', u'Асбест', u'Асино', u'Аскиз', u'Астрахань', u'Аткарск', u'Атяшево', u'Афипский', u'Ахтубинск', u'Ахтырский', u'Ачинск', u'Аша', u'Бавлы', u'Багаевская', u'Базарный Карабулак', u'Байкальск', u'Баймак', u'Бакал', u'Бакалы', u'Баксан', u'Балабаново', u'Балакирево', u'Балаково', u'Балахна', u'Балашиха', u'Балашов', u'Балезино', u'Балтийск', u'Барабинск', u'Барвиха', u'Барда', u'Барнаул', u'Барыш', u'Барышево', u'Батайск', u'Батырево', u'Бачатский', u'Башмаково', u'Бежецк', u'Безенчук', u'Белая Глина', u'Белая дача', u'Белая Калитва', u'Белая Холуница', u'Белгород', u'Белебей', u'Белинский', u'Белово', u'Белогорск', u'Белокуриха', u'Белоозерский', u'Белорецк', u'Белореченск', u'Белореченский', u'Белоярский', u'Белоярский (Свердловская область)', u'Белый Яр', u'Бердигестях', u'Бердск', u'Березник', u'Березники', u'Березовка', u'Березовский (СИБ)', u'Березовский(Урал)', u'Беслан', u'Бийск', u'Бикин', u'Биробиджан', u'Бирск', u'Бисерть', u'Бичура', u'Благовещенка', u'Благовещенск', u'Благовещенск(ДВ)', u'Благодарный', u'Бобров', u'Богатое', u'Богданович', u'Богородицк', u'Богородск', u'Боготол', u'Богучаны', u'Богучар', u'Бодайбо', u'Бокситогорск', u'Бологое', u'Болотное', u'Болхов', u'Большая Глушица', u'Большая Мартыновка', u'Большая Мурта', u'Большая Черниговка', u'Большеречье', u'Большеустьикинское', u'Большие Вязёмы', u'Большое Сорокино', u'Большой Камень', u'Бор', u'Борзя', u'Борисково', u'Борисовичи', u'Борисовка', u'Борисоглебск', u'Боровичи', u'Боровск', u'Боровский', u'Борогонцы', u'Бородино', u'Борское', u'Братск', u'Бронницы', u'Брюховецкая', u'Брянск', u'Бугры', u'Бугульма', u'Бугуруслан', u'Буденновск', u'Буздяк', u'Бузулук', u'Буинск', u'Буй', u'Буйнакск', u'Бутурлиновка', u'Быково', u'Быково (Волгоградская область)', u'Валдай', u'Валуйки', u'Варгаши', u'Варна', u'Великие Луки', u'Великий Новгород', u'Великий Устюг', u'Вельск', u'Венев', u'Верещагино', u'Верея', u'Верх-Чебула', u'Верхневилюйск', u'Верхнеднепровский', u'Верхнеуральск', u'Верхнеяркеево', u'Верхний Уфалей', u'Верхняя Пышма', u'Верхняя Салда', u'Верхняя Тура', u'Верхотурье', u'Вешенская', u'Вешки', u'Видное', u'Вилюйск', u'Вилючинск', u'Винзили', u'Витим', u'Витязево', u'Вихоревка', u'Вичуга', u'Владивосток', u'Владикавказ', u'Владимир', u'Власиха', u'Вознесенское', u'Волгоград', u'Волгодонск', u'Волгореченск', u'Волжск', u'Волжский', u'Вологда', u'Володарск', u'Володарский', u'Волоколамск', u'Волоконовка', u'Волосово', u'Волхов', u'Волчанск', u'Вольск', u'Воргашор', u'Воркута', u'Воронеж', u'Ворсма', u'Воскресенск', u'Восточный', u'Воткинск', u'Всеволожск', u'Вурнары', u'Выборг', u'Выкса', u'Вырица', u'Выселки', u'Высокая гора', u'Высоковск', u'Вышний Волочек', u'Вяземский', u'Вязники', u'Вязьма', u'Вятские Поляны', u'Гаврилов-Ям', u'Гагарин', u'Гаджиево', u'Газопровод', u'Гай', u'Галич', u'Гатчина', u'Гвардейск', u'Геленджик', u'Георгиевск', u'Глазов', u'Глушково', u'Говорово', u'Голицыно', u'Голышманово', u'Горки-10', u'Горно-Алтайск', u'Горнозаводск', u'Горный', u'Горняк', u'Городец', u'Городище', u'Городище', u'Городище (Волгоградская область)', u'Гороховец', u'Горьковка', u'Горячий Ключ', u'Грайворон', u'Грамотеино', u'Грачёвка', u'Гремячинск', u'Грозный', u'Грязи', u'Грязовец', u'Губаха', u'Губкин', u'Губкинский', u'Гудермес', u'Гуково', u'Гулькевичи', u'Гурьевск (Калининградская область)', u'Гурьевск (Кемеровская область)', u'Гусев', u'Гусево', u'Гусиноозерск', u'Гусь-Хрустальный', u'ГЭС', u'д. Воронки', u'д. Лапино', u'д. Новосаратовка', u'Давлеканово', u'Дагомыс', u'Далматово', u'Дальнегорск', u'Дальнереченск', u'Данилов', u'Данков', u'Де-Кастри', u'Дегтярск', u'Дедовск', u'Демидов', u'Демянск', u'Дербент', u'Десногорск', u'Джалиль', u'Джубга', u'Дзержинск', u'Дзержинск (Иркутская область)', u'Дзержинский', u'Дивеево', u'Дивногорск', u'Дивное', u'Димитровград', u'Динская', u'Динской', u'Дмитриев', u'Дмитров', u'Дно', u'Доброе', u'Добрянка', u'Довольное', u'Долгодеревенское', u'Долгопрудный', u'Долинск', u'Домбаровский', u'Домодедово', u'Донецк', u'Донской', u'Дорогобуж', u'Дорохово', u'Дрезна', u'Дубна', u'Дубовка', u'Дубовое', u'Дубовское', u'Дубровицы', u'Дудинка', u'Дюртюли', u'Дятьково', u'Егорлыкская', u'Егорьевск', u'Ейск', u'Екатеринбург', u'Елабуга', u'Елань', u'Елец', u'Елизово', u'Елино', u'Ельня', u'Еманжелинск', u'Ембаево', u'Емва', u'Енисейск', u'Ерино', u'Ермолино', u'Ершов', u'Ессентуки', u'Ефремов', u'Железноводск', u'Железногорск (Курская область)', u'Железногорск Красноярский кр.', u'Железногорск-Илимский', u'Железнодорожный', u'Жердевка', u'Жигулевск', u'Жирновск', u'Жуков', u'Жуковка', u'Жуковский', u'Забайкальск', u'Завитинск', u'Заводоуковск', u'Заволжск', u'Заволжье', u'Завьялово', u'Задонск', u'Заинск', u'Закадье Волгоград', u'Закадье Новосиб', u'Закадье РнД', u'Закадье СПб', u'Закаменск', u'Залари', u'Замкадье Москва', u'Заозерный', u'Заозерск', u'Западная Двина', u'Западный', u'Заполярный', u'Запрудня', u'Зарайск', u'Заречный (Пензенская область)', u'Заречный (Свердловская область)', u'Заринск', u'Засечное', u'Заюково', u'Звенигово', u'Звенигород', u'Зверево', u'Зеленогорск', u'Зеленогорск (СПб)', u'Зеленоград', u'Зеленоградск', u'Зеленодольск', u'Зеленокумск', u'Зеленчукская', u'Земетчино', u'Зерноград', u'Зея', u'Зима', u'Зимовники', u'Златоуст', u'Змеиногорск', u'Знаменск', u'Зубова Поляна', u'Зубцов', u'Ибреси', u'Ивангород', u'Иваново', u'Ивантеевка', u'Ивдель', u'Иглино', u'Игра', u'Ижевск', u'Избербаш', u'Излучинск', u'Изобильный', u'Икряное', u'Иланский', u'Илек', u'Иловля', u'Ильинский', u'Ильский', u'им.Воровского', u'Инжавино', u'Инза', u'Иноземцево', u'Инской', u'Инта', u'Ипатово', u'Ирбит', u'Иркутск', u'Исетское', u'Исилькуль', u'Искитим', u'Истра', u'Ишим', u'Ишимбай', u'Йошкар-Ола', u'Кабанск', u'Кабардинка', u'Кавалерово', u'Кавказская', u'Кагальницкая', u'Кадуй', u'Казанское', u'Казань', u'Кайеркан', u'Калач', u'Калач', u'Калач-на-Дону', u'Калачинск', u'Калашниково', u'Калининград', u'Калининец', u'Калинино', u'Калининск', u'Калининская', u'Калтан', u'Калуга', u'Калязин', u'Камбарка', u'Каменка', u'Каменка (Воронежская область)', u'Каменск-Уральский', u'Каменск-Шахтинский', u'Камень на Оби', u'Камень-на-Оби', u'Камешково', u'Камские Поляны', u'Камызяк', u'Камышин', u'Камышлов', u'Канаш', u'Кандалакша', u'Каневецкий', u'Каневская', u'Канск', u'Карабаново', u'Карабаш', u'Караваево', u'Караево', u'Карасук', u'Карачаевск', u'Карачев', u'Каргаполье', u'Каргат', u'Каргополь', u'Кармаскалы', u'Карпинск', u'Карсун', u'Карталы', u'Карымское', u'Касимов', u'Каскара', u'Касли', u'Каспийск', u'Катав-Ивановск', u'Катайск', u'Качканар', u'Кашин', u'Кашира', u'Кез', u'Кемерово', u'Кемь', u'Кизел', u'Кизляр', u'Кизнер', u'Кимовск', u'Кимры', u'Кингисепп', u'Кинель', u'Кинель-Черкассы', u'Кинешма', u'Киргиз-Мияки', u'Киреевск', u'Киренск', u'Киржач', u'Кириши', u'Киров', u'Киров (Калужская область)', u'Кировград', u'Кирово-Чепецк', u'Кировск', u'Кировск (Лен.обл)', u'Кировский', u'Кирс', u'Кирсанов', u'Киселевск', u'Кисловодск', u'Климово', u'Климовск', u'Клин', u'Клинцы', u'Ключи', u'Клявлино', u'Ковдор', u'Ковров', u'Ковылкино', u'Когалым', u'Кодинск', u'Козельск', u'Козловка', u'Козьмодемьянск', u'Кола', u'Коломна', u'Колпашево', u'Колпино', u'Колтуши', u'Колывань', u'Колышлей', u'Кольцово', u'Кольчугино', u'Коммунар', u'Коммунарка', u'Комсомольск', u'Комсомольск-на-Амуре', u'Комсомольский', u'Конаково', u'Кондопога', u'Кондрово', u'Константиновск', u'Копейск', u'Кораблино', u'Кореновск', u'Коркино', u'Королев', u'Коротчаево', u'Корсаков', u'Коряжма', u'Костомукша', u'Кострома', u'Котельники', u'Котельниково', u'Котельнич', u'Котлас', u'Котово', u'Котовск', u'Кохма', u'Кочубеевское', u'Кошки', u'Красково', u'Красная Горбатка', u'Красноармейск', u'Красноармейск(МО)', u'Краснобродский', u'Красновишерск', u'Красногорск', u'Красногорский', u'Краснодар', u'Красное Село', u'Красное-на-Волге', u'Краснозаводск', u'Краснознаменск', u'Краснокаменск', u'Краснокамск', u'Краснообск', u'Краснослободск', u'Краснослободск (Волгоградская область)', u'Краснотурьинск', u'Красноуральск', u'Красноусольский', u'Красноуфимск', u'Красноярск', u'Красноярский', u'Красный Бор', u'Красный Кут', u'Красный Сулин', u'Красный Яр (Астраханская область)', u'Красный Яр (Самарская область)', u'Кременки', u'Кременкуль', u'Криводановка', u'Кромы', u'Кронштадт', u'Кропоткин', u'Крыловская', u'Крымск', u'Кстово', u'Кубинка', u'Кувандык', u'Кувшиново', u'Кудрово', u'Кудымкар', u'Куеда', u'Кузнецк', u'Кузоватово', u'Кузьмоловский', u'Куйбышев', u'Куйтун', u'Кукмор', u'Кулаково', u'Кулебаки', u'Кулунда', u'Кумертау', u'Кунгур', u'Курагино', u'Курган', u'Курганинск', u'Куровское', u'Курск', u'Куртамыш', u'Курумоч', u'Курчатов', u'Куса', u'Кушва', u'Кушнаренково', u'Кущевская', u'Кызыл', u'Кыштым', u'Кяхта', u'Лабинск', u'Лабытнанги', u'Ладожская', u'Лазаревское', u'Лакинск', u'Лангепас', u'Лебедянь', u'Лев Толстой', u'Лежнево', u'Ленинградская', u'Лениногорск', u'Ленинск-Кузнецкий', u'Ленинское', u'Ленск', u'Лермонтово', u'Лесной', u'Лесной городок', u'Лесозаводск', u'Лесосибирск', u'Ливны', u'Ликино-Дулево', u'Лиман', u'Линево', u'Липецк', u'Лисий Нос', u'Лиски', u'Лихославль', u'Лобня', u'Лодейное Поле', u'Локоть', u'Ломоносов', u'Лосино-Петровский', u'Лотошино', u'Луга', u'Луговое', u'Луза', u'Лукоянов', u'Лунино', u'Луховицы', u'Лысково', u'Лысьва', u'Лыткарино', u'Льгов', u'Люберцы', u'Людиново', u'Лянтор', u'Магадан', u'Магдагачи', u'Магнитогорск', u'Майкоп', u'Майма', u'Майский', u'Майя', u'Максатиха', u'Макушино', u'Малаховка', u'Малая Вишера', u'Малмыж', u'Малоярославец', u'Мамадыш', u'Мамоново', u'Мамонтово', u'Мамоны', u'Мамыри', u'Мантурово', u'Мари-Турек', u'Мариинск', u'Маркова', u'Маркс', u'Марфино', u'Маслянино', u'Матвеев Курган', u'Мга', u'Мегион', u'Медведево', u'Медвежьегорск', u'Медногорск', u'Медынь', u'Междуреченск', u'Междуреченский', u'Меленки', u'Мелеуз', u'Мельниково', u'Менделеево', u'Менделеевск', u'Мензелинск', u'Месягутово', u'Металлострой', u'Миасс', u'Микунь', u'Миллерово', u'Минеральные Воды', u'Минусинск', u'Миньяр', u'Мирный (Архангельская область)', u'Мирный (Самарская область)', u'Мирный (Якутия)', u'Михайлов', u'Михайловка', u'Михайловка (Башкортостан)', u'Михайловск (Свердловская область)', u'Михайловск (Ставропольский край)', u'Михайловское', u'Михнево', u'Мичуринск', u'Могойтуй', u'Могоча', u'Можайск', u'Можга', u'Моздок', u'Мокшан', u'Молодежный', u'Молочный', u'Монино', u'Мончегорск', u'Морки', u'Морозовск', u'Моршанск', u'Москва', u'Московский', u'Московский (Тюменская область)', u'Мосрентген', u'Мостовской', u'Мраково', u'Мулино', u'Муравленко', u'Мурино', u'Мурманск', u'Мурмаши', u'Муром', u'Муромцево', u'Мценск', u'Мыски', u'Мытищи', u'Набережные Челны', u'Навашино', u'Навля', u'Нагорный', u'Надым', u'Назарово', u'Назрань', u'Нальчик', u'Намцы', u'Нариманов', u'Наро-Фоминск', u'Нарткала', u'Нарьян-Мар', u'Нахабино', u'Находка', u'Невель', u'Невельск', u'Невинномысск', u'Невьянск', u'Некрасовский', u'Нелидово', u'Немчиновка', u'Ненецкий автономный округ (Архангельская область)', u'Нерехта', u'Нерчинск', u'Нерюнгри', u'Нефтегорск', u'Нефтекамск', u'Нефтекумск', u'Нефтеюганск', u'Нижнебаканская', u'Нижневартовск', u'Нижнедевицк', u'Нижнекамск', u'Нижнесортымский', u'Нижнеудинск', u'Нижние Серги', u'Нижний Бестях', u'Нижний Ингаш', u'Нижний Ломов', u'Нижний Новгород', u'Нижний Тагил', u'Нижняя Салда', u'Нижняя Тура', u'Николаевск', u'Николаевск-на-Амуре', u'Никольск', u'Никольское', u'Новая Адыгея', u'Новая Ладога', u'Новая Ляля', u'Новая Разводная', u'Новая Усмань', u'Новоаганск', u'Новоалександровск', u'Новоалтайск', u'Новоаннинский', u'Новобурейск', u'Новобурейский', u'Нововоронеж', u'Новодвинск', u'Новое Девяткино', u'Новозавидовский', u'Новозыбков', u'Новоивановское', u'Новокубанск', u'Новокузнецк', u'Новокуйбышевск', u'Новомихайловский', u'Новомичуринск', u'Новомосковск', u'Новониколаевский', u'Новоорск', u'Новопавловск', u'Новопокровская', u'Новопокровский', u'Новороссийск', u'Новосергиевка', u'Новосергиевский пс', u'Новосибирск', u'Новоспасское', u'Новотитаровская', u'Новотроицк', u'Новоузенск', u'Новоуральск', u'Новохоперск', u'Новочебоксарск', u'Новочеркасск', u'Новошахтинск', u'Новый городок', u'Новый Оскол', u'Новый Уренгой', u'Ногинск', u'Ноглики', u'Нолинск', u'Норильск', u'Ноябрьск', u'Нурлат', u'Нытва', u'Нюрба', u'Нягань', u'Нязепетровск', u'Няндома', u'Обливская', u'Облучье', u'Обнинск', u'Оболенск', u'Обоянь', u'Обухово', u'Обь', u'Одинцово', u'Озерный', u'Озерск', u'Озеры', u'Озинки', u'Октябрьск', u'Октябрьский', u'Октябрьский (Архангельская область)', u'Октябрьский (Волгоградская область)', u'Октябрьский (МО)', u'Октябрьский (Пермский край)', u'Октябрьское', u'Олекминск', u'Оленегорск', u'Олонец', u'Омск', u'Омутинское', u'Омутнинск', u'Онега', u'Опочка', u'Орда', u'Ордынский', u'Орел', u'Оренбург', u'Орехово-Зуево', u'Оричи', u'Орлово-Кубанский', u'Орловский', u'Орск', u'Оса', u'Осинники', u'Осиновая Гора', u'Осиново', u'Остафьево', u'Осташков', u'Остров', u'Острогожск', u'Отрадная', u'Отрадное', u'Отрадный', u'Оха', u'Очер', u'П. Ключи', u'п. Краснозерское', u'п. Михнево', u'п. Отрадное', u'п.Врангель', u'п.Лучегорск', u'п.Солнечный', u'Павло-Слободское', u'Павловка', u'Павлово', u'Павловск (Алтай)', u'Павловск (Воронежская область)', u'Павловск (СПб)', u'Павловская', u'Павловская Слобода', u'Павловский Посад', u'Падерина', u'Палласовка', u'Пангоды', u'Парголово', u'Партизанск', u'Парфино', u'Патрушева', u'Пашино', u'Пенза', u'Первомайск', u'Первомайский', u'Первомайский (Оренбургская область)', u'Первоуральск', u'Переволоцкий', u'Переделкино', u'Пересвет', u'Переславль-Залесский', u'Переяславка', u'Пермь', u'Перхушково', u'Песочное', u'Пестово', u'Петергоф', u'Петров Вал', u'Петровск', u'Петровск-Забайкальский', u'Петровская', u'Петрозаводск', u'Петропавловск-Камчатский', u'Петухово', u'Петушки', u'Печора', u'Печоры', u'Пикалево', u'Питкяранта', u'Плавск', u'Пласт', u'Пластунка', u'Плесецк', u'Поворино', u'Погар', u'Пограничный', u'Подольск', u'Подпорожье', u'Пойковский', u'Покачи', u'Покров', u'Покровка', u'Покровск', u'Покровское', u'Полазна', u'Полевской', u'Полесск', u'Полтавская', u'Полтавский', u'Полысаево', u'Полярные Зори', u'Полярный', u'Поронайск', u'пос. Ванино', u'пос. Прогресс', u'пос.Кола', u'пос.Лоо', u'пос.Славянка', u'Поспелиха', u'Похвистнево', u'Почеп', u'Починки', u'Починок', u'Поярково', u'Правдинский', u'Приволжск', u'Приволжье', u'Приморск', u'Приморско-Ахтарск', u'Приобье', u'Приозерск', u'Приютово', u'Прокопьевск', u'Пролетарск', u'Промышленная', u'Протвино', u'Прохладный', u'Прохоровка', u'Псков', u'Пугачев', u'Пугачевский', u'Пурпе', u'Пустошка', u'Путилково', u'Пушкин', u'Пушкино', u'Пущино', u'Пыть-Ях', u'Пятигорск', u'Радужный', u'Радужный (Владимирская область)', u'Раевский', u'Развилка', u'Райчихинск', u'Раменское', u'Расковский', u'Рассказово', u'Ребриха', u'Ревда', u'Редкино', u'Реж', u'Репино', u'Реутов', u'Рефтинский', u'Решетникова', u'Ржавки', u'Ржев', u'Родино', u'Родники', u'Рославль', u'Россошь', u'Ростов', u'Ростов-на-Дону', u'Рошаль', u'Рощино', u'Ртищево', u'Рубцовск', u'Рудня', u'Руза', u'Рузаевка', u'Румянцево', u'Рыбинск', u'Рыбное', u'Рыздвяный', u'Рыльск', u'Ряжск', u'Рязань', u'Садовый', u'Сакмара', u'Салават', u'Саларьево', u'Салехард', u'Сальск', u'Самара', u'Санкт-Петербург', u'Саракташ', u'Саранск', u'Сарапул', u'Саратов', u'Саров', u'Сасово', u'Сатка', u'Сафоново', u'Саяногорск', u'Саянск', u'Светлогорск', u'Светлоград', u'Светлые Горы', u'Светлый', u'Светогорск', u'Свирск', u'Свободный', u'Себеж', u'Северо-Енисейский', u'Северобайкальск', u'Северодвинск', u'Североморск', u'Североуральск', u'Северск', u'Северская', u'Севск', u'Сегежа', u'Селенгинск', u'Селижарово', u'Сельцо', u'Селятино', u'Семенов', u'Семикаракорск', u'Семилуки', u'Сергач', u'Сергиев Посад', u'Сергиевск', u'Сердобск', u'Серебряные пруды', u'Серов', u'Серпухов', u'Сертолово', u'Серышево', u'Сестрорецк', u'Сибай', u'Сибирцево', u'Сиверский', u'Сим', u'Сковородино', u'Скопин', u'Славгород', u'Славянск-на-Кубани', u'Сланцы', u'Слободской', u'Слюдянка', u'Смирных', u'Смоленск', u'Смоленское', u'Смоленщина', u'Снежинск', u'Снежногорск', u'Собинка', u'Советск', u'Советск (Кировская область)', u'Советская Гавань', u'Советский', u'Совхоз им Ленина', u'Сокол', u'Соликамск', u'Солнечногорск', u'Солнечный', u'Солнечный (Хабаровский край)', u'Солнечный (Ханты-Мансийский АО)', u'Солонцы', u'Соль-Илецк', u'Сольцы', u'Сорочинск', u'Сортавала', u'Сосенский', u'Сосенское', u'Сосновка', u'Сосновоборск', u'Сосновый Бор', u'Сосногорск', u'Софрино', u'Сочи', u'Спас-Клепики', u'Спасск', u'Спасск-Дальний', u'Спасск-Рязанский', u'Среднеуральск', u'Ставрополь', u'Становое', u'Старая Купавна', u'Старая Русса', u'Старица', u'Старовеличковская', u'Стародуб', u'Староминская', u'Старощербиновская', u'Старый Оскол', u'Степное', u'Стерлитамак', u'Стрежевой', u'Стрельна', u'Строитель', u'Струнино', u'Ступино', u'Суворов', u'Суджа', u'Судогда', u'Суздаль', u'Суземка', u'Сузун', u'Суксун', u'Сунжа', u'Сунтар', u'Сураж', u'Сургут', u'Суровикино', u'Сухиничи', u'Суходол', u'Сухой Лог', u'Сходня', u'Сызрань', u'Сыктывкар', u'Сысерть', u'Сясьстрой', u'Тавда', u'Таврическое', u'Таганрог', u'Тайга', u'Тайшет', u'Таксимо', u'Талакан', u'Талдом', u'Талица', u'Талнах', u'Таловая', u'Тальменка', u'Таманский', u'Тамань', u'Тамбов', u'Тамбовка', u'Тара', u'Тарасовский', u'Тарко-Сале', u'Таруса', u'Татарск', u'Татищево', u'Тахтамукай', u'Ташла', u'Таштагол', u'Тбилисская', u'Тверь', u'Тейково', u'Тельмана', u'Темников', u'Темрюк', u'Тербуны', u'Терема', u'Тетюши', u'Тимашевск', u'Тисуль', u'Тихвин', u'Тихорецк', u'Тобольск', u'Товарково', u'Тогучин', u'Токсово', u'Толбазы', u'Толмачёво', u'Тольятти', u'Томилино', u'Томск', u'Топки', u'Топчиха', u'Торбеево', u'Торжок', u'Торопец', u'Тосно', u'Тотьма', u'Тоцкое Второе', u'Трехгорный', u'Троицк', u'Троицк (Москва)', u'Троицк (Челябинская область)', u'Троицко-Печорск', u'Троицкое', u'Трубчевск', u'Трудобеликовский', u'Трудовое', u'Туапсе', u'Тугулым', u'Туймазы', u'Тула', u'Тулун', u'Туринск', u'Тутаев', u'Тучково', u'Тымовское', u'Тында', u'Тырныауз', u'Тюкалинск', u'Тюльган', u'Тюмень', u'Тяжинский', u'Ува', u'Уваровка', u'Уварово', u'Увельский', u'Углич', u'Угловское', u'Удачный', u'Удельная', u'Удомля', u'Ужур', u'Узловая', u'Улан-Удэ', u'Ульяновск', u'Унеча', u'Упорово', u'Урай', u'Уральский', u'Урдома', u'Уренгой', u'Урень', u'Уржум', u'Урмары', u'Уруссу', u'Урюпинск', u'Усинск', u'Усмань', u'Усолье-Сибирское', u'Успенское', u'Уссурийск', u'Усть-Абакан', u'Усть-Джегута', u'Усть-Донецкий', u'Усть-Илимск', u'Усть-Катав', u'Усть-Кут', u'Усть-Лабинск', u'Усть-Нера', u'Усть-Ордынский', u'Устюжна', u'Уфа', u'Ухта', u'Учалы', u'Учкекен', u'Уяр', u'Фатеж', u'Федино', u'Федоровский', u'Федоскино', u'Федяково', u'Фокино', u'Фролово', u'Фрязево', u'Фрязино', u'Фряново', u'Фурманов', u'Хабаровск', u'Хабары', u'Хадыженск', u'Хандыга', u'Ханты-Мансийск', u'Ханты-Мансийский АО - Югра', u'Харабали', u'Харп', u'Хвалынск', u'Хилок', u'Химки', u'Хлевное', u'Холмск', u'Холмская', u'Хор', u'Хотьково', u'Хохол', u'Целина', u'Цемдолина', u'Цивильск', u'Цимлянск', u'Циолковский', u'Чайковский', u'Чалтырь', u'Чамзинка', u'Чапаевск', u'Чаплыгин', u'Чарышское', u'Чебаркуль', u'Чебоксары', u'Чегдомын', u'Чекмагуш', u'Челно-Вершины', u'Челябинск', u'Чемал', u'Чердынь', u'Черемхово', u'Черепаново', u'Череповец', u'Черкесск', u'Черниговка', u'Черноголовка', u'Черногорск', u'Чернушка', u'Черный Яр', u'Чернышевск', u'Чернянка', u'Черняховск', u'Чесноковка', u'Чехов', u'Чистополь', u'Чита', u'Чишмы', u'Чкаловск', u'Чудово', u'Чунский', u'Чурапча', u'Чусовой', u'Шадринск', u'Шакша', u'Шаля', u'Шарлык', u'Шарыпово', u'Шарья', u'Шатки', u'Шатура', u'Шаховская', u'Шахты', u'Шахунья', u'Шацк', u'Шебекино', u'Шелехов', u'Шентала', u'Шерегеш', u'Шигоны', u'Шилка', u'Шилово', u'Шимановск', u'Шипуново', u'Шира', u'Шкотово', u'Шлиссельбург', u'Шолохово', u'Шумерля', u'Шумиха', u'Шушары', u'Шушенское', u'Шуя', u'Щапово', u'Щедрино', u'Щекино', u'Щелково', u'Щепкин', u'Щербинка', u'Щигры', u'Щучье', u'Ытык-Кюёль', u'Эжва', u'Электрогорск', u'Электросталь', u'Электроугли', u'Элиста', u'Энгельс', u'Энем', u'Эстосадок', u'Юбилейный', u'Югорск', u'Юдино (Московская область)', u'Южа', u'Южно-Сахалинск', u'Южноуральск', u'Юрга', u'Юрьев-Польский', u'Юрюзань', u'Яблоновский', u'Ядрин', u'Яйва', u'Якутск', u'Ялуторовск', u'Ямало-Ненецкий АО', u'Янаул', u'Янтарный', u'Яр', u'Яранск', u'Яровое', u'Ярославль', u'Ярцево', u'Ясногорск', u'Ясный', u'Яхрома', u'Яшкино', u'Яя',
        ] 

    @classmethod
    def change_showcases_category(self, company, cheque_id, showcases_category_id):
        cheque = FNSCheque.objects.get(company=company, id=cheque_id)
        showcases_category = ShowcasesCategory.objects.get(id=showcases_category_id)
        cheque.showcases_category = showcases_category
        cheque.save()

    @classmethod
    def create_and_save_cheque_from_text(cls, company, p0, p1, p2, p3):
	c = FNSCheque(is_manual=True, company=company, fns_totalSum=p0, manual_what=p1, manual_where=p2, fns_dateTime=p3)
        c.save()
        return c
        
    @classmethod
    def create_fns_cheque_from_qr_text(cls, qr_text, company):
        if cls.has_cheque_with_qr_text(company, qr_text):
            #Такой чек уже существует'
            print u'Alert: We has this cheque in this company!'
            assert False
	qr_params = QRCodeReader.qr_text_to_params(qr_text)
        if len(qr_params.keys()) != 5:
            assert False
	cheque_params = QRCodeReader.qr_params_to_cheque_params(qr_params)
	return FNSCheque(is_manual=False, company=company, fns_fiscalDocumentNumber=cheque_params['fns_fiscalDocumentNumber'], fns_fiscalDriveNumber=cheque_params['fns_fiscalDriveNumber'], fns_fiscalSign=cheque_params['fns_fiscalSign'], fns_dateTime=cheque_params['fns_dateTime'], fns_totalSum=cheque_params['fns_totalSum'])

    @classmethod
    def create_save_update_fns_cheque_from_proverkacheka_com(cls, qr_text, company):
	fns_cheque = FNSCheque.create_fns_cheque_from_qr_text(qr_text, company)
        #TODO проверить что такого чека еще нет в этой окмпании а то получается 2 раза один и тот же чек добавить
	fns_cheque.save()
        fns_cheque_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params('', qr_text)
	#FNSCheque.update_cheque_from_json(fns_cheque, fns_cheque_json)
	fns_cheque.update_cheque_from_json(fns_cheque_json)
        fns_cheque.set_best_category_if_high_rating()
        return fns_cheque

    @classmethod
    def current_city_title(cls, company):
        for fns_cheque in cls.objects.filter(company=company).order_by('-fns_dateTime'):
            for city in cls.__cities():
	        if re.findall(u'г.' + city + u',', fns_cheque.get_shop_info_string()):
                    #return u'г.' + city + u','
                    return city
	        if re.findall(u'г. ' + city + u',', fns_cheque.get_shop_info_string()):
                    #return u'г.' + city + u','
                    return city
        print 'Error: NED FIX CITY '
        return 'Moscow'

    @classmethod
    def find_cheques_in_company_with_inn(cls, company, user_inn):
        return list(FNSCheque.objects.filter(company=company, fns_userInn=user_inn)[:3000])

    @classmethod
    def find_cheques_in_company_with_user(cls, company, user):
        cheques = []
        for c in FNSCheque.objects.filter(company=company)[:3000]:
            if user == c.get_user():
                cheques.append(c)
        return cheques

    def format_date_qr_srt(self):
        #return str(self.fns_dateTime[0:4]) + str(self.fns_dateTime[5:7]) + str(self.fns_dateTime[8:10]) + 'T' + str(self.fns_dateTime[11:13]) + str(self.fns_dateTime[14:16]) 
        return str(self.fns_dateTime[8:10]) + str(self.fns_dateTime[5:7]) + str(self.fns_dateTime[0:4]) + 'T' + str(self.fns_dateTime[11:13]) + str(self.fns_dateTime[14:16]) 

    def format_fns_dateTime_2_DateTime(self):
        return  datetime.strptime(self.fns_dateTime, '%Y-%m-%dT%H:%M:%S')

    def format_sum_qr_srt(self):
        return str(self.fns_totalSum[0:-2]) + '.' + str(self.fns_totalSum[-2:])

    def get_address(self):
        if self.is_manual:
            return self.manual_where

        #add = self.fns_cheque.json["document"]["receipt"]["retailAddress"]
        #add = self.fns_cheque.json['json']["retailAddress"]
        #add = ast.literal_eval(json.loads(self.fns_cheque.json))['json']

        #addd = self.fns_cheque.json

        #if not self.fns_cheque.json or not ast.literal_eval(self.fns_cheque.json).has_key('data'):
        if not self.json or not ast.literal_eval(self.json).has_key('data'):
        #if not self.json or not json.loads(self.json).has_key('data'):
            print 'Error: not find json or json["data"]'
            return
        
        #addd = ast.literal_eval(self.fns_cheque.json)['data']['json']
        addd = ast.literal_eval(self.json)['data']['json']
        #'retailAddress', u'buyerPhoneOrAddress',  retailPlaceAddress
        k = 0
        if addd.has_key('retailPlaceAddress'):
            k += 1
            #print '--1'
        if addd.has_key('retailAddress'):
            k += 1
            #print '--2'
        #if addd.has_key(u'buyerPhoneOrAddress') and addd.get('buyerPhoneOrAddress') not in ['', 'k.a.vakulin@mail.ru', 'l.krylova@muz-lab.ru','yuriy_per@yahoo.com']:
        #    k += 1
        #    print '--3'

        if k > 1:
            #print addd.keys()
            #print addd.get('retailPlaceAddress', '').encode('utf8')
            #print addd.get('retailAddress', '').encode('utf8')
            #print addd.get('buyerPhoneOrAddress', '').encode('utf8')
            #print '----'
            assert False

        if addd.has_key('retailPlaceAddress'):
            add = addd['retailPlaceAddress']
        elif addd.has_key('retailAddress'):
            add = addd['retailAddress']
        #elif addd.has_key(u'buyerPhoneOrAddress'):
        #    add = addd[u'buyerPhoneOrAddress']
        else:
            #print '+++ k=', k
            #print addd.get(u'buyerPhoneOrAddress')
            #print addd.keys()
            add = ''
            #assert False
        #add = addd['json']
#        print add.encode('utf8')
        #get_retailAddress
        return add

    @classmethod
    def get_cheque_with_qr_text(cls, company, qr_text):
	qr_params = QRCodeReader.qr_text_to_params(qr_text)
        if len(qr_params.keys()) != 5:
            assert False
	cheque_params = QRCodeReader.qr_params_to_cheque_params(qr_params)

        fiscalDocumentNumber = cheque_params['fns_fiscalDocumentNumber']
        fiscalDriveNumber = cheque_params['fns_fiscalDriveNumber']
        fiscalSign = cheque_params['fns_fiscalSign']
        dateTime = cheque_params['fns_dateTime']
        totalSum = cheque_params['fns_totalSum']

        return FNSCheque.objects.get(
            company=company,
            fns_fiscalDocumentNumber=fiscalDocumentNumber,
            fns_fiscalDriveNumber=fiscalDriveNumber,
            fns_fiscalSign=fiscalSign,
            fns_dateTime__contains=dateTime,
            fns_totalSum=totalSum)

    @classmethod
    def get_cheque_with_fns_cheque_json(cls, company, fns_cheque_json):
        fiscalDocumentNumber = fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"]
        fiscalDriveNumber = fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"]
        fiscalSign = fns_cheque_json["document"]["receipt"]["fiscalSign"]
        dateTime = fns_cheque_json["document"]["receipt"]["dateTime"]
        totalSum = fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')

        return FNSCheque.objects.get(
            company=company,
            fns_fiscalDocumentNumber=fiscalDocumentNumber,
            fns_fiscalDriveNumber=fiscalDriveNumber,
            fns_fiscalSign=fiscalSign,
            fns_dateTime__contains=dateTime,
            fns_totalSum=totalSum)

    def get_datetime(self):
        return self.fns_dateTime

    def get_operator(self):
        if not self.json or not ast.literal_eval(self.json).has_key('data'):
            print 'Error: not find json or json["data"]'
            return
        
        addd = ast.literal_eval(self.json)['data']['json']
        k = 0
        if addd.has_key('operator'):
            k += 1

        if k > 1:
            assert False

        if addd.has_key('operator'):
            add = addd['operator']
        else:
            add = ''
        return add

    @classmethod
    def get_recomended_showcases_category_2_rating(cls, company, fns_cheque, increment):
        scs = {}
        inn_cheques = FNSCheque.find_cheques_in_company_with_inn(company, fns_cheque.get_user_inn()) if fns_cheque.get_user_inn() else[]
        user_cheques = FNSCheque.find_cheques_in_company_with_user(company, fns_cheque.get_user()) if fns_cheque.get_user() else []
        for c in inn_cheques + user_cheques:
            if c.showcases_category:
                if not scs.has_key(c.showcases_category):
                    scs[c.showcases_category] = 0
                scs[c.showcases_category] += increment
        return scs

    def get_recomended_showcases_category(self):
        scs = {}
        #inn_cheques = FNSCheque.find_cheques_in_company_with_inn(self.company, self.get_user_inn()) if self.get_user_inn() else[]
        #user_cheques = FNSCheque.find_cheques_in_company_with_user(self.company, self.get_user()) if self.get_user() else []
        #for c in inn_cheques + user_cheques:
        #    if c.showcases_category:
        #        if not scs.has_key(c.showcases_category):
        #            scs[c.showcases_category] = 0
        #        scs[c.showcases_category] += 20

        increment = 20
        showcases_category_2_rating = FNSCheque.get_recomended_showcases_category_2_rating(self.company, self, increment)
        for k in showcases_category_2_rating.keys():
            if not scs.has_key(k):
                scs[k] = 0
            scs[k] += showcases_category_2_rating[k]

        #for company in Company.objects.filter(employees__in=self.company.employees.all()): 
        #    inn_cheques = FNSCheque.find_cheques_in_company_with_inn(company, self.get_user_inn()) if self.get_user_inn() else []
        #    user_cheques = FNSCheque.find_cheques_in_company_with_user(company, self.get_user()) if self.get_user() else []
        #    for c in inn_cheques + user_cheques:
        #        if c.showcases_category:
        #            if not scs.has_key(c.showcases_category):
        #                scs[c.showcases_category] = 0
        #            scs[c.showcases_category] += 1
 
        increment = 1
        for company in Company.objects.filter(employees__in=self.company.employees.all()): 
            showcases_category_2_rating = FNSCheque.get_recomended_showcases_category_2_rating(company, self, increment)
            for k in showcases_category_2_rating.keys():
                if not scs.has_key(k):
                    scs[k] = 0
                scs[k] += showcases_category_2_rating[k]

        if len(scs.keys()) == 0:
            if ShowcasesCategory.objects.count() > 0 and ShowcasesCategory.objects.filter(id=1).count() > 0:
                return ShowcasesCategory.objects.get(id=1)
            else:
                print 'Alert: Only for test!'
                return ShowcasesCategory(title='Time test', id=1)

        sort_scs = sorted(scs.items(), key=lambda x : x[1])

        best_category = sort_scs[-1][0]
        return best_category

        #if ShowcasesCategory.objects.count():
        #    return ShowcasesCategory.objects.get(id=1)
        #else:
        #    print 'Alert: Only for test!'
        #    return ShowcasesCategory(title='Time test', id=1)

    def get_shop_short_info_string(self):
        if self.get_user():
            return self.get_user()
        elif self.get_address():
            return self.get_address()
        elif self.get_user_inn():
            #return 'ИНН ' + self.get_user_inn() + ' ' + self.get_operator()
            return self.get_user_inn()
        else:
            return

    def get_shop_info_string(self):
        return 'МАГАЗИН: ' + self.get_user() + ' ИНН: ' + self.get_user_inn() + ' АДРЕС: ' + self.get_address()

    def get_user(self):
        if not self.json or not ast.literal_eval(self.json).has_key('data'):
            print 'Error: not find json or json["data"]'
            return ''
        
        addd = ast.literal_eval(self.json)['data']['json']
        k = 0
        if addd.has_key('user'):
            k += 1

        if k > 1:
            assert False

        if addd.has_key('user'):
            add = addd['user']
        else:
            add = ''
        return add

    def get_user_inn(self):
        return self.fns_userInn

    @staticmethod
    def import_from_proverkacheka_com_format_like_fns(qr_text, company):
        qr_params = QRCodeReader.qr_text_to_params(qr_text)
        if len(qr_params.keys()) != 5:
            print 'Error: Not enough params'
            return
        #fns_cheque_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params(cheque)
        fns_cheque_json = ImportProverkachekaComFormatLikeFNS.get_fns_cheque_by_qr_params(qr_params, qr_text)

        if not fns_cheque_json:
            print 'Error: not good json!'
            return

        #if FNSCheque.has_cheque_with_fiscal_params(company,  
        #    fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"],
        #    fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"],
        #    fns_cheque_json["document"]["receipt"]["fiscalSign"],
        #    fns_cheque_json["document"]["receipt"]["dateTime"],
        #    fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')):
        #    print u'Alert: We has this cheque!'
        #    #Такой чек уже существует'
        #    return
        if FNSCheque.has_cheque_with_fns_cheque_json(company, fns_cheque_json):
            return

        FNSCheque.save_cheque_from_fns_cheque_json(company, fns_cheque_json)

    @classmethod
    def has_cheque_with_fiscal_params(cls, company, fiscalDocumentNumber, fiscalDriveNumber, fiscalSign, dateTime, totalSum):
        if FNSCheque.objects.filter(
            company=company,
            fns_fiscalDocumentNumber=fiscalDocumentNumber,
            fns_fiscalDriveNumber=fiscalDriveNumber,
            fns_fiscalSign=fiscalSign,
            fns_dateTime__contains=dateTime,
            fns_totalSum=totalSum).count() > 0:
            print '---has cheque----------'
            print FNSCheque.objects.get(
            company=company,
            fns_fiscalDocumentNumber=fiscalDocumentNumber,
            fns_fiscalDriveNumber=fiscalDriveNumber,
            fns_fiscalSign=fiscalSign,
            fns_dateTime__contains=dateTime,
            fns_totalSum=totalSum)
            return True

        #for cheque in FNSCheque.objects.filter(
        #    company=company,
        #    fns_fiscalDocumentNumber=fiscalDocumentNumber,
        #    fns_fiscalDriveNumber=fiscalDriveNumber,
        #    fns_fiscalSign=fiscalSign,
        #    fns_dateTime__contains=dateTime,
        #    fns_totalSum=totalSum):
        #    print '---has cheque----------'
        #    print cheque
        #    return True
        return False

    @classmethod
    def has_cheque_with_qr_text(cls, company, qr_text):
	qr_params = QRCodeReader.qr_text_to_params(qr_text)
        if len(qr_params.keys()) != 5:
            assert False
	cheque_params = QRCodeReader.qr_params_to_cheque_params(qr_params)
        return FNSCheque.has_cheque_with_params(company, cheque_params)

    @classmethod
    def has_cheque_with_params(cls, company, cheque_params):
        return FNSCheque.has_cheque_with_fiscal_params(company, 
            cheque_params['fns_fiscalDocumentNumber'],
            cheque_params['fns_fiscalDriveNumber'],
            cheque_params['fns_fiscalSign'],
            cheque_params['fns_dateTime'],
            cheque_params['fns_totalSum'])

    @classmethod
    def has_cheque_with_fns_cheque_json(cls, company, fns_cheque_json):
        if FNSCheque.has_cheque_with_fiscal_params(company,  
            fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"],
            fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"],
            fns_cheque_json["document"]["receipt"]["fiscalSign"],
            fns_cheque_json["document"]["receipt"]["dateTime"],
            fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')):
            print u'Alert: We has this cheque!'
            #Такой чек уже существует'
            return True
        return False

    @classmethod
    def save_cheque_from_fns_cheque_json(cls, company, fns_cheque_json):
        """
        fix надо разделить на три метода:
            1 сохраннеие в базу
            2 создать(если такого еще нет) товары на основе имеющихся продуктов
            2 привязка к позиции в чеке товарв
        """
        if not fns_cheque_json:
            return 

        account = None
        #if cls.has_cheque_with_fiscal_params(company,
        #    fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"],
        #    fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"],
        #    fns_cheque_json["document"]["receipt"]["fiscalSign"],
        #    fns_cheque_json["document"]["receipt"]["dateTime"],
        #    fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')):
        #    print u'Alert: Find same cheque!'
        #    assert False
        if cls.has_cheque_with_fns_cheque_json(company, fns_cheque_json):
            assert False

        # везде добавил временуж зону Москва timezone
        datetime_buy = fns_cheque_json["document"]["receipt"]["dateTime"] + '+03:00'

        #fns_cheque = FNSCheque(
        #    company=company,
        #    json=fns_cheque_json,
        #    fns_userInn=fns_cheque_json["document"]["receipt"]["userInn"],
        #    fns_dateTime=datetime_buy
        #)
        fns_cheque = FNSCheque()
        fns_cheque.company = company
        fns_cheque.fns_dateTime = datetime_buy
        fns_cheque.is_manual = False
        fns_cheque.save()

        #cls.update_cheque_from_json(fns_cheque, fns_cheque_json)
        fns_cheque.update_cheque_from_json(fns_cheque_json)
        fns_cheque.set_best_category_if_high_rating()

    def set_best_category_if_high_rating(self):
        ball_for_set_by_default = 5
        increment = 1
        self = FNSCheque.objects.get(id=self.id)
        scs = FNSCheque.get_recomended_showcases_category_2_rating(self.company, self, increment)
        if len(scs.keys()) > 0:
            sort_scs = sorted(scs.items(), key=lambda x : x[1])
            best_category = sort_scs[-1][0]
            best_category_rating = sort_scs[-1][1]

            if best_category_rating > ball_for_set_by_default:
                self.showcases_category = best_category
                self.save()

    #@classmethod
    #def update_cheque_from_json(cls, fns_cheque, fns_cheque_json):
    def update_cheque_from_json(self, fns_cheque_json):
        #fns_cheque.json = fns_cheque_json
        self.json = fns_cheque_json
        #fns_cheque.fns_userInn = fns_cheque_json["document"]["receipt"]["userInn"]
        self.fns_userInn = fns_cheque_json["document"]["receipt"]["userInn"]

        #fns_cheque.fns_fiscalDocumentNumber = fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"]
        #fns_cheque.fns_fiscalDriveNumber = fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"]
        #fns_cheque.fns_fiscalSign = fns_cheque_json["document"]["receipt"]["fiscalSign"]
        #fns_cheque.fns_dateTime = fns_cheque_json["document"]["receipt"]["dateTime"]
        #fns_cheque.fns_totalSum = fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')
        self.fns_fiscalDocumentNumber = fns_cheque_json["document"]["receipt"]["fiscalDocumentNumber"]
        self.fns_fiscalDriveNumber = fns_cheque_json["document"]["receipt"]["fiscalDriveNumber"]
        self.fns_fiscalSign = fns_cheque_json["document"]["receipt"]["fiscalSign"]
        self.fns_dateTime = fns_cheque_json["document"]["receipt"]["dateTime"]
        self.fns_totalSum = fns_cheque_json["document"]["receipt"].get("totalSum", 'Error')

        #fns_cheque.save()
        self.save()

        for elemnt in fns_cheque_json["document"]["receipt"].get("items", []):
            #Сначало можно попытаться найти найти товар с таким же названием и пустыми поялми чтобы лишний раз не делать одно и тоже
            #fns_cheque_element = FNSChequeElement(
            #    fns_cheque=fns_cheque,
            #    quantity=elemnt.get("quantity"),
            #    name=elemnt.get("name"),
            #    price=elemnt.get("price"),
            #    sum=elemnt.get("sum"),
            #)
            #fns_cheque_element.save()

            try:
                #fns_cheque_element = FNSChequeElement(
                #    fns_cheque=fns_cheque,
                #    quantity=elemnt.get("quantity"),
                #    name=elemnt.get("name"),
                #    price=elemnt.get("price"),
                #    sum=elemnt.get("sum"),
                #)
                fns_cheque_element = FNSChequeElement(
                    fns_cheque=self,
                    quantity=elemnt.get("quantity"),
                    name=elemnt.get("name"),
                    price=elemnt.get("price"),
                    sum=elemnt.get("sum"),
                )
                fns_cheque_element.save()
            except:
                import traceback
                traceback.print_exc()
                #traceback.print_exception()
                import sys
                print sys.exc_info()
                traceback.print_exception(*sys.exc_info())
                #traceback.print_stack()
                print '------------'

    def __unicode__(self):
        return u"FNSCheque = FDN: %s, FD: %s, FS: %s, DT: %s, TS: %s" % (self.fns_fiscalDocumentNumber, self.fns_fiscalDriveNumber, self.fns_fiscalSign, self.fns_dateTime, self.fns_totalSum)

class FNSChequeElement(models.Model):
    """
    нужно учитывать весовой товар
    цена за штуку
    {"quantity":2,"sum":11980,"price":5990,"name":"4607045982771 МОЛОКО SPAR УЛЬТРАПА"}
    {"quantity":0.205,"sum":7770,"price":37900,"name":"259 АВОКАДО ВЕСОВОЕ"}

    {"weight": 220, "quantity":1,"sum":13500,"price":13500,"name":u"4607004891694 СЫР СЛИВОЧНЫЙ HOCHLA", "volume": 0.22},
    """
    fns_cheque = models.ForeignKey(FNSCheque)
    name = models.CharField(blank=True, null=True, max_length=254)
    price = models.SmallIntegerField(blank=True, null=True) # цена за штуку или за 1000 грамм
    quantity = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=3) # штуки или граммы
    sum = models.SmallIntegerField(blank=True, null=True) # финальная цена

    # пользователь сам указывает по данной позиции этот параметр
    volume = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=3) # указываем 1 если весовой товар или вес одной штуки в килошраммах

    def consumption_element_params(self):
        #if self.volume * self.quantity != self.get_weight_from_title():
        #    print self.volume * self.quantity, '!=', self.get_weight_from_title()
        #if float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))) != self.get_weight_from_title():
        #    print float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))), '!=', self.get_weight_from_title()

        #print 'weight:',
        #print self.volume * self.quantity,
        #print float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))),
        #print self.get_weight_from_title()
        return {
            'title': self.get_title(),
            'datetime': self.fns_cheque.get_datetime(),
            #'weight': float(self.volume * self.quantity),
            'weight': self.get_weight(),
        }

    def get_address(self):
        return self.fns_cheque.get_address()


    def get_datetime(self):
        return self.fns_cheque.get_datetime()

    def get_price(self):
        #return self.price * self.quantity
        return self.price

    def get_quantity(self):
        #print type(self.quantity)
        return int(self.quantity) if self.quantity == int(self.quantity) else self.quantity

    def get_sum(self):
        return self.sum

    def get_price_per_one_gram(self):
        if int(self.price * self.quantity) != int(self.sum) and (int(self.price * self.quantity) + 1) != int(self.sum):
            print 'Error: price * quantity != sum.', (int(self.price * self.quantity) + 1), '!=', int(self.sum)
            print 'Error: price * quantity != sum.', self.price * float(self.quantity), '!=', self.sum
        if not self.get_weight():
            return None
        return float("{0:.2f}".format(self.price * float(self.quantity) / self.get_weight()))

    def get_title(self):
        return self.name

    def get_weight(self):
        if self.__has_weight_from_title() and self.volume:
            if float(self.__get_weight_from_title()) == float(self.volume):
                return float(self.volume * self.quantity)
            else:
                print 'Error: Not rigth weight!'
                assert False
        elif self.__has_weight_from_title():
            return float(self.__get_weight_from_title() * float(self.quantity))
        elif self.volume:
            return float(self.volume * self.quantity)
        else:
#            print 'Error: Not have weight!'
            return None
            assert False
            return float(self.quantity)

    def get_weight_from_title(self):
        """
        только для тестов
        """
        print 'Alert: only in test!'
        return self.__get_weight_from_title()

    def __get_weight_from_title(self):
        #1кг 0.224 None
        #Сыр ЛЕБЕДЕВСКАЯ АФ Кавказский по-домашнему мягкий бзмж 45% 300г 1.000 None
        #LAYS Из печи Чипсы карт нежн сыр с 2.000 None
        #Чипсы LAY'S Sticks Сыр чеддер 125г 1.000 None
        return float("{0:.3f}".format(IsPackedAndWeight.weight_from_cheque_title(self.name) / 1000))

    def is_element_piece(self):
        print 'TODO need fix'
        q = self.get_quantity()
        if float(q) == float(int(q)) and not self.__has_weight_from_title:
            return True
        return False
        #return self.__has_weight_from_title()
        #return True

    def has_weight(self):
        """
        только для тестов
        """
        print 'Alert: only in test!'
        return self.__has_weight_from_title()

    def has_weight_from_title(self):
        """
        только для тестов
        """
        print 'Alert: only in test!'
        return self.__has_weight_from_title()

    def __has_weight_from_title(self):
        #return False if IsPackedAndWeight.weight_from_cheque_title(self.name) == 0 else True
        return IsPackedAndWeight.has_weight_from_cheque_title(self.name)

    def list_string_for_search(self):
        title = self.name

        result = set()
        result.add((100, title))

        #TODO рассмотрим несколько случаев 
        #Когда первое слово цифра(небольшое число) - номер позиции в чеке
        #среденее число или число со зведочной (3452541 или *3452541) серийный номер в данной компании
        #большое чилсло - штрих код или в компании или общий
        #слово - чаще одно но иногода и 2 идущие подрят именно в такой последовательности - так принято в индустриии
    
        list_int = re.findall(u'^\*?(\d+) (\d+)', title)
        if len(list_int) and len(list_int[0]) > 1:
            title = ' '.join(title.split(' ')[2:])
            if len(list_int[0][0]) > 5 and len(list_int[0][1]) > 5:
                string = list_int[0][0] + ' ' + list_int[0][1]
                result.add((95, string))
            elif len(list_int[0][0]) < 5 and len(list_int[0][1]) > 5:
                string = list_int[0][1]
                result.add((93, string))

        list_int = re.findall(u'^\*?(\d+)', title)
        if len(list_int):
            title = ' '.join(title.split(' ')[1:])
            if len(list_int[0][0]) > 5:
                string =  list_int[0][0]
                result.add((92, string))

        #100 балов если сопала вся строка
        #90 балов если совпали 3 первых слова
        #80 балов если совпало 2 первых слова
        #70 - порог до которго показываем
        #60 балов если совпало первое слов

        words = title.split(' ')
        if len(words) > 2:
            string = words[0] + ' ' + words[1] + ' ' + words[2]
            result.add((90, string))

        if len(words) > 1:
            string = words[0] + ' ' + words[1]
            result.add((80, string))

        #if len(words) > 0:
        #    string = words[0]
        #    result.add((60, string))

        return result


    def offer_element_params(self):
        #print self.get_title().encode('utf8'), self.fns_cheque.get_datetime(), self.sum, self.volume, self.quantity
        #if self.volume * self.quantity != self.get_weight_from_title():
        #    print self.volume * self.quantity, '!=', self.get_weight_from_title()
        #if float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))) != self.get_weight_from_title():
        #    print float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))), '!=', self.get_weight_from_title()

        #print 'weight:',
        #print self.volume * self.quantity,
        #print float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))),
        #print self.get_weight_from_title()
        return {
            'title': self.get_title(),
            'datetime': self.fns_cheque.get_datetime(),
            #'weight': float(self.volume * self.quantity),
            #'weight': self.get_weight(),
            #'price_per_weight': float("{0:.3f}".format(self.sum / ((self.volume if self.volume else 1) * self.quantity))),
            'price_per_weight': float("{0:.3f}".format(self.sum / self.get_weight())),
        }

    def __str__(self):
        return (self.name.encode('utf8') if self.name else '') + str(' ') + str(self.quantity) + str(' ') + str(self.volume) + str(' ') + str(self.sum) + str(' ') + str(self.price)# + self.name.encode('utf8') 
 
class QRCodeReader(object):
    @classmethod
    def is_it_qr_text(cls, text):
        el = text.split('&')
        if len(el) < 5 or len(el) > 9:
            return False
        for e in el:
            if len(e.split('=')) != 2:
                return False

        cheque = {}
        for e in text.split('&'):
            k, v = e.split('=')
            if k == 't':
                cheque['date'] = v
	        #cheque['date'] = str(datetime.strptime(v, '%Y%m%dT%H%M'))
            elif k == 's':
                cheque['sum'] = str(int(float(v)*100))
            elif k == 'fn':
                cheque['FN'] = v
            elif k == 'fp':
                cheque['FDP'] = v
            elif k == 'i':
                cheque['FD'] = v

        if len(cheque.keys()) != 5:
            return False

        return True

    @classmethod
    def qr_text_to_params(cls, text):
        if not cls.is_it_qr_text(text):
            return {}

        cheque = {}
        for e in text.split('&'):
            k, v = e.split('=')
            if k == 't':
                cheque['date'] = v
	        #cheque['date'] = str(datetime.strptime(v, '%Y%m%dT%H%M'))
            elif k == 's':
                cheque['sum'] = str(int(float(v)*100))
            elif k == 'fn':
                cheque['FN'] = v
            elif k == 'fp':
                cheque['FDP'] = v
            elif k == 'i':
                cheque['FD'] = v
        return cheque

    @classmethod
    def convert_data(cls, d):
        return d[0:4] + '-' + d[4:6] + '-' + d[6:11] + ':' + d[11:13] + ':' + d[13:15]

    @classmethod
    def qr_params_to_cheque_params(cls, qr_params):
        return {
            'fns_fiscalDocumentNumber': qr_params['FD'],
            'fns_fiscalDriveNumber': qr_params['FN'],
            'fns_fiscalSign': qr_params['FDP'],
            'fns_dateTime': cls.convert_data(qr_params['date']),
            'fns_totalSum': qr_params['sum'],
        }

    @classmethod
    def has_5_params_for_create_cheque(cls, s):
        p = cls.parse_1(s)
        for k in ['s', 'fn', 'fp', 'i', 't']:
            if not p.has_key(k):
                return False
        return True

    @classmethod
    def parse_1(cls, s1):
	t2 = s1.split(' ')
	p = {}
	for j in t2:
	    s = re.findall(u'^(\d+\.\d{1,2})$', j)
	    fn = re.findall(u'^(\d{16})$', j)
	    fp = re.findall(u'^(\d{9,10})$', j)
	    i = re.findall(u'^(\d{1,6})$', j)
	    time = re.findall(u'^(\d{1,2}\:\d{1,2}\:?\d{0,2})$', j)
	    date_1 = re.findall(u'^(\d{4}\.\d{1,2}\.\d{1,2})$', j)
	    date_2 = re.findall(u'^(\d{1,2}\.\d{1,2}\.\d{4})$', j)
	    date_time = re.findall(u'^(\d{8}T\d{1,2}\d{1,2}\d{0,2})$', j)
	    #'20201216T1818 29.00 9280440301295284 236 3107860384',

	    if s:
		p['s'] = re.findall(u'^(\d+\.\d{1,2})$', j)[0]
	    elif fn:
		p['fn'] = re.findall(u'^(\d{16})$', j)[0]
	    elif fp:
		p['fp'] = re.findall(u'^(\d{9,10})$', j)[0]
	    elif i:
		p['i'] = re.findall(u'^(\d{1,6})$', j)[0]
	    elif time:
		p['time'] = re.findall(u'^(\d{1,2}\:\d{1,2}\:?\d{1,2})$', j)[0]
	    elif date_1:
		p['date'] = re.findall(u'^(\d{4}\.\d{1,2}\.\d{1,2})$', j)[0]
	    elif date_2:
		p['date'] = re.findall(u'^(\d{1,2}\.\d{1,2}\.\d{4})$', j)[0]
		p['date'] = p['date'][6:10] + p['date'][3:5] + p['date'][0:2]
            elif date_time:
                p['date'] = re.findall(u'^(\d{8})T', j)[0]
                p['time'] = re.findall(u'T(\d{1,2}\d{1,2}\d{0,2})$', j)[0]
	    else:
		#print u'Alert not identify: %s' % j.encode('utf8')
		#print u'Alert not identify: %s' % j
		#print u'Alert not identify: ' + j
                pass

	    #if not p['s']:
	    #p['s'] = re.findall(u'^(\d+\.\d{1,2})$', i)

	#p['s'] = re.findall(u'(\d+\.\d{1,2})', s1)[0]
	#p['fn'] = re.findall(u'(\d{16})', s1)[0]
	#p['fp'] = re.findall(u'(\d{9,10})', s1)[0]
	#p['i'] = re.findall(u'(\d{1,6})', s1)[0]
	#p['time'] = re.findall(u'(\d{1,2}\:\d{1,2}\:?\d{1,2})', s1)[0]
	#p['date'] = re.findall(u'(\d{4}\.\d{1,2}\.\d{1,2})', s1)[0]

        if p.has_key('date') and p.has_key('time'):
    	    p['t'] = ''.join(p['date'].split('.')) + 'T' + ''.join(p['time'].split(':'))
    	    del p['time']
	    del p['date']
	
        return p

class ImportProverkachekaComFormatLikeFNS(object):
    """
    Класс отвечающий за импорт данных из ФНС России
    """

    @classmethod
    def get_fns_cheque_by_qr_params(cls, cheque, qr_text):
        #https://proverkacheka.com/check/get?fn=9288000100159749&fd=14492&fp=2104555358&n=1&s=293.90&t=05.12.2020+22%3A06&qr=0
        #url = 'https://proverkacheka.com/check/get?fn=' + cheque['FN'] + '&fd=' + cheque['FD'] + '&fp=' + cheque['FDP'] + '&n=1&s=' + cheque['sum'] + '&t=' + cheque['date'] + '&qr=0'
        #print url
	#webUrl = urllib.urlopen(url)
	#data = webUrl.read()
	#print "result code: " + str(webUrl.getcode()) 
	#print data

	req = urllib2.Request('https://proverkacheka.com/check/get')
        da = urllib.urlencode({
            #'qrraw': 't=20201107T2058&s=63.00&fn=9288000100192401&i=439&fp=2880362760&n=1',
            'qrraw': qr_text,
            'qr': 3,
        })
        data = urllib2.urlopen(url=req, data=da).read()
        #time.sleep(1)
        #print data

        # удалил блок html
        #data = '{"code":1,"data":{"json":{"code":3,"items":[{"nds":2,"sum":6300,"name":"Чизбургер с луком СБ","price":6300,"ndsSum":573,"quantity":1,"paymentType":4,"productType":1}],"nds10":573,"userInn":"7729532221","dateTime":"2020-11-07T20:58:00","kktRegId":"0000677159011474","operator":"Тамаева Минара","totalSum":6300,"creditSum":0,"fiscalSign":2880362760,"prepaidSum":0,"shiftNumber":6,"cashTotalSum":0,"provisionSum":0,"ecashTotalSum":6300,"operationType":1,"requestNumber":203,"fiscalDriveNumber":"9288000100192401","fiscalDocumentNumber":439,"fiscalDocumentFormatVer":2},"html":""}}'

        #return json.loads(data)
        fns_cheque_json = json.loads(data)

        #if not type(fns_cheque_json) is dict or \
        #    not fns_cheque_json.get('data') or \
        #    not type(fns_cheque_json['data']) is dict or \
        #    not fns_cheque_json['data'].get('json'):
        if not type(fns_cheque_json) is dict or not type(fns_cheque_json['data']) is dict:
            print u'Alert: This is not good JSON!'
            return

        fns_cheque_json["document"] = {}
        fns_cheque_json["document"]["receipt"] = fns_cheque_json['data']['json']

        return fns_cheque_json

class IsPackedAndWeight(object):
    """
    Для чеков на терриротии России
    по строке из  чека определяем является товар "весовым" - продаюзимся на вес или "упаковочны"
        и если он упаковочный пробуем вытащить из это сроки размер упаковки.
    """
    @classmethod
    def __create_words_from_cheque_title(cls, title):
        #title = title.replace('.',' ').replace('(',' ').replace(')',' ')

        #title = title.replace('.',' ') # Ащан для разделения слов, которые они сократили, использует точки. Просто так нельзя делать так как есть товар "Напиток б/а PEPSI жесть 0.33L"

        result = re.findall(u'(\d+\.\d+)', title)
        #print '========>>>>'
        #print 'title =', title.encode('utf8')
        #print 'len(result)=', len(result)
        #assert False
        #print 'result =', result
        if len(result) > 1:
            print title.encode('utf8')
            print result
            #TODO обнаружили такую запись в позиции чека
            #Пакетный тур, Турция, Сиде, IRON AMBASSADOR SIDE BEACH, 14.07.2019 - 23.07.2019
            #[u'14.07', u'23.07']
            return []
            assert False
        elif len(result) == 1:
            result_update = result[0].replace('.',',')
            #print 'result_update =', result_update
            title = title.replace(result[0], ' ' + result_update)
            #print 'title =', title.encode('utf8')

        title = title.replace('.',' ')
        #print 'title =', title.encode('utf8')
        #print '<<========'

        words = []
        for word in title.split():
            #word = word.replace('.','').replace('(','').replace(')','')
            word = word.replace(',','.')
            word = word.upper()
            #if len(word) > 2:
            if len(word) > 1: # не проходит "2L" из "Напиток б/а PEPSI Light с/газ  2L"
                words.append(word)
        return words

    @classmethod
    def __get_weight_in_gram_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_gram(word)
        if result:
            weight = int(result[0])
            return weight
        else:
            assert False

    @classmethod
    def __get_weight_in_kilogram_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_kilogram(word)
        if result:
            weight = float(result[0])*1000
            return weight
        else:
            assert False

    @classmethod
    def __get_weight_in_litr_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_litr(word)
        if result:
            weight = float(result[0])*1000
            return weight
        else:
            assert False

    @classmethod
    def has_weight_from_cheque_title(cls, title):
        for word in cls.__create_words_from_cheque_title(title):
            if cls.__has_weight_in_gram_for_title(word) or \
                cls.__has_weight_in_kilogram_for_title(word) or \
                cls.__has_weight_in_litr_for_title(word):
                return True
        else:
            return False
        #OLD version
        try:
            w = cls.weight_from_cheque_title(title)
            return True
        except:
            import traceback
            traceback.print_exc()
            #traceback.print_exception()
            import sys
            print sys.exc_info()
            traceback.print_exception(*sys.exc_info())
            #traceback.print_stack()
            print '------------'

            return False

    @classmethod
    def __has_weight_in_gram_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_gram(word)
        if result:
            return True
        else:
            return False

    @classmethod
    def __has_weight_in_kilogram_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_kilogram(word)
        if result:
            return True
        else:
            return False

    @classmethod
    def __has_weight_in_litr_for_title(cls, word):
        result = cls.__prepare_date_for_match_weight_in_litr(word)
        if result:
            return True
        else:
            return False

    #@classmethod
    #def is_packed_from_cheque_title(cls, title):
    #    for word in cls.__create_words_from_cheque_title(title):
    #        if cls.__has_weight_in_gram_for_title(word):
    #            is_packed = True
    #            break
    #        elif cls.__has_weight_in_kilogram_for_title(word):
    #            is_packed = True
    #            break
    #        else:
    #            is_packed = False
    #    return is_packed

    @classmethod
    def __prepare_date_for_match_weight_in_gram(cls, word):
        result_g = re.findall(u'^(\d+)г$', word)
        result_gg = re.findall(u'^(\d+)Г$', word)
        result_gr = re.findall(u'^(\d+)гр$', word)
        result_grgr = re.findall(u'^(\d+)ГР$', word)
        return result_g + result_gg + result_gr + result_grgr

    @classmethod
    def __prepare_date_for_match_weight_in_kilogram(cls, word):
        #result_kg = re.findall(u'^(\d*.&\d+)кг$', word)
        result_kg = re.findall(u'^(\d*\.?\d+)кг$', word)
        result_kgkg = re.findall(u'^(\d*\.?\d+)КГ$', word)
        return result_kg + result_kgkg

    @classmethod
    def __prepare_date_for_match_weight_in_litr(cls, word):
        result_l = re.findall(u'^(\d*\.?\d+)л$', word)
        result_ll = re.findall(u'^(\d*\.?\d+)Л$', word)
        result_lll = re.findall(u'^(\d*\.?\d+)L$', word)
        result_llll = re.findall(u'^(\d*\.?\d+)l$', word)
        #print 'word =',word.encode('utf8')
        #print result_l + result_ll + result_lll + result_llll
        return result_l + result_ll + result_lll + result_llll

    @classmethod
    def weight_from_cheque_title(cls, title):
        for word in cls.__create_words_from_cheque_title(title):
            if cls.__has_weight_in_gram_for_title(word):
                weight = cls.__get_weight_in_gram_for_title(word)
                break
            elif cls.__has_weight_in_kilogram_for_title(word):
                weight = cls.__get_weight_in_kilogram_for_title(word)
                break
            elif cls.__has_weight_in_litr_for_title(word):
                weight = cls.__get_weight_in_litr_for_title(word)
                break
        else:
            assert False
            print 'Alert: not find weight!'
            return 0
        return float("{0:.3f}".format(float(weight)))
        #return float(weight)



