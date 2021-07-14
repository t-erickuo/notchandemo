import abc
import threading
from datetime import datetime

import logging
LOG = logging.getLogger(__name__)

class SessionProtocol(abc.ABC):

    def __init__(self):
        self._notification_lock = threading.Lock()
        self._completed = {}
        self._notifications = {}
    
    def __enter__(self):
        self.open()

    def __exit__(self, *args, **kwargs):
        self.close()

    @abc.abstractmethod
    def open(self):
        raise NotImplementedError()

    def wait(self, *, response, **kwargs):
        notification_id = self.extract_notification(response)
        with self._notification_lock:
            if notification_id in self._completed:
                # LOG.critical(f'{notification_id} was already completed... returning immediately!')
                return
            else:
                # LOG.critical(f'Registering for notifications for {notification_id}')
                event = threading.Event()
                self._notifications[notification_id] = event
        event.wait()
        # LOG.critical(f'{notification_id} completed!')

    def close(self):
        LOG.critical(f'Closing notification channel {self}')
        with self._notification_lock:
            while self._notifications:
                notification_id, event = self._notifications.popitem()
                LOG.critical(f'Completing pending notification because I am closing: {notification_id}')
                event.set()

    @abc.abstractmethod
    def extract_notification(self, response):
        raise NotImplementedError()

    def on_connection_lost(self):
        pass

    def on_completion(self, notification_id, data):
        # utc_time = datetime.utcnow()
        # LOG.critical(f'Signalling {notification_id} as completed at {utc_time}')
        with self._notification_lock:
            self._completed[notification_id] = data
            try:
                existing = self._notifications.pop(notification_id)
                existing.set()
            except KeyError:
                pass    
    