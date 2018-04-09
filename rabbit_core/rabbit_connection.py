import logging

import pika
import rabbit_config

LOGGER = logging.getLogger(__name__)

class RabbitWrapper(object):

    __slots__ = (
        "_rabbit_params",
        "_connection",
        "_channel",
        "_closing",
        "_queues",
        "_queues_declared"
    )

    def __init__(self, rabbit_params):
        LOGGER.debug("__init__ called")
        self._rabbit_params = rabbit_params

        self._connection = None
        self._channel = None
        self._closing = False
        self._queues = []
        self._queues_declared = 0

    def add_queue_definition(self, queue_definition):
        LOGGER.debug("Adding queue definition: %s", queue_definition.name)
        self._queues.append(queue_definition)

    def connect(self):
        LOGGER.debug("Connection to %s", self._rabbit_params.host)
        self._connection = pika.SelectConnection(pika.ConnectionParameters(host=self._rabbit_params.host),
                                                 on_open_callback=self._on_connection_open,
                                                 stop_ioloop_on_close=False)
        self._connection.ioloop.start()


    def _on_connection_open(self, unusued_connection):
        LOGGER.debug("Connection successfully opened")
        self._connection.add_on_close_callback(self._on_connection_closed)
        self._open_channel()

    def _on_connection_closed(self, connection, close_code, close_text):
        LOGGER.info("Connection closed: %s - %s", close_code, close_text)

        self._queues_declared = 0
        self._channel = None

        if self._closing:
            self._connection.ioloop.stop()
            return

        LOGGER.info("Reconnecting in %d seconds", self._rabbit_params.retry_delay)
        self._connection.add_timeout(self._rabbit_params.rety_delay, self._reconnect)

    def _reconnect(self):

        # Stop previous ioloop
        self._connection.ioloop.stop()

        if self._closing:
            return

        self.connect()

    def _open_channel(self):
        LOGGER.debug("Opening channel")
        self._connection.channel(on_open_callback=self._on_channel_opened)

    def _on_channel_opened(self, channel):
        LOGGER.debug("Channel opened successfully")
        self._channel = channel
        self._setup_exchange()

    def _setup_exchange(self):
        LOGGER.debug("Declaring exchange '%s'", self._rabbit_params.exchange)
        self._channel.exchange_declare(self._on_exchange_declareok, self._rabbit_params.exchange)

    def _on_exchange_declareok(self, unused_frame):
        LOGGER.debug("Exchange declared successfully")
        self._setup_queues()

    def _setup_queues(self):
        LOGGER.debug("Declaring %d queues", len(self._queues))

        for queue in self._queues:
            LOGGER.debug("Declaring queue: name=%s routing_key=%s", queue.name, queue.routing_key)
            self._channel.queue_declare(lambda _: self._on_queue_declareok(queue), queue.name)

    def _on_queue_declareok(self, queue):
        LOGGER.debug("Queue declared successfully: %s", queue.name)
        LOGGER.debug("Binding queue %s to routing key '%s", queue.name, queue.routing_key)
        self._channel.queue_bind(lambda _: self._on_bind_queueok(queue),
                                 queue.name,
                                 self._rabbit_params.exchange,
                                 queue.routing_key)

    def _on_bind_queueok(self, queue_defintion):
        LOGGER.debug("Queue '%s' bound to routing key '%s' successfully", queue_defintion.name, queue_defintion.routing_key)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    client = RabbitWrapper(rabbit_config.RabbitConnectionParameters(host="localhost"))
    client.add_queue_definition(rabbit_config.QueueDefinition(name="test",routing_key="test.route"))
    client.connect()