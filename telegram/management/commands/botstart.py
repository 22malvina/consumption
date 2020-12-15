from django.core.management.base import BaseCommand
from django.utils import timezone
from telegram.models import Telegram

class Command(BaseCommand):
    help = 'Displays current time'

    def handle(self, *args, **kwargs):
	while True:
	    Telegram.process_last_messages_from_bot()
