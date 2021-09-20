from abc import abstractmethod
from enum import Enum


class Message:
    def __init__(self, descriptor, content):
        self.descriptor = descriptor
        self.content = content


class AbstractWorker:
    config = None
    inbox_queue = None
    outbox_queue = None

    class InboxTypes(Enum):
        pass

    class OutboxTypes(Enum):
        pass

    @abstractmethod
    def __init__(self, config, inbox_queue, outbox_queue, *args, **kwargs):
        self.config = config
        self.inbox_queue = inbox_queue
        self.outbox_queue = outbox_queue
        pass

    @abstractmethod
    def _handle_message(self, message):
        pass

    def handle_incoming(self):
        message = self.inbox_queue.get()
        response = self._handle_message(message)
        if response is not None:
            self.outbox_queue.put(response)


def start_worker(worker_class, config, inbox_queue, outbox_queue, *args, **kwargs):
    worker = worker_class(config, inbox_queue, outbox_queue, *args, **kwargs)

    while True:
        worker.handle_incoming()
