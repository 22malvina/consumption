from django.core.management.base import BaseCommand
from django.utils import timezone
from telegram.models import Telegram

from sentry_sdk import capture_exception
from sentry_sdk import start_transaction

import time

class Command(BaseCommand):
    help = 'Displays current time'

    def handle(self, *args, **kwargs):
	while True:
	    #Telegram.process_last_messages_from_bot()

	    #with start_transaction(op="task", name='ART Telegram.process_last_messages_from_bot()'):
	    with start_transaction(op="task"):
		try:
		    Telegram.process_last_messages_from_bot()
                #except:
		except Exception as e:
		    import traceback
		    traceback.print_exc()
		    import sys
		    print sys.exc_info()
		    traceback.print_exception(*sys.exc_info())
		    print '------------sleep-----'
		    time.sleep(15)
		    print '------------'

		    capture_exception(e)


