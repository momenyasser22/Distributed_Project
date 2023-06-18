import pika
from threading import Lock
from connection import ConnectionHandle
from messageParser import serializeJSON, deserializeJSON


class Consumer:

    def __init__(self, server) -> None:
        self.server = server
        self.lock = Lock()
        self.handles = {}

    def subscribe(self, exchange, event_handler=lambda a, b, c, d: print(d), deserializer=lambda x: x):
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.server, heartbeat=0, credentials=pika.PlainCredentials("ubuntu", "ubuntu")
                                      ))
        channel = connection.channel()
        queue = channel.queue_declare(
            queue='', auto_delete=True, exclusive=True)
        queueName = queue.method.queue
        connectionHandle = ConnectionHandle(
            connection=connection, channel=channel, exchange=exchange, queue=queueName)
        channel.queue_bind(queue=queueName, exchange=exchange)
        channel.basic_consume(queue=queueName, on_message_callback=self.createCallback(
            event_handler, deserializer))
        self.handles[exchange] = connectionHandle
        self.start_consuming(exchange=exchange)

    def __defaultHandler(self, channel, method, properties, body):
        print(body)

    def start_consuming(self, exchange):
        self.handles[exchange].start()

    def stop_consuming(self, exchange):
        self.handles[exchange].stop()

    def createCallback(self, handler, deserializer, *args):
        """ 
        this creates the appropriate handler to messages
        it takes a handler and a deserializer and creates
        a new function that deserializes the message first then
        gives it to the handler.
        also, it adds a mutex lock on the handler to make it 
        thread safe. this means the consumer object can't handle
        more than one event at a time
        """
        if handler is None:
            handler = self.__defaultHandler

        def safe(*args):
            # args are supposed to be 4. the last one is the message body
            msg = deserializer(args[-1])
            self.lock.acquire(1)
            # args* is a tuple and they are immutable. so we do it this way.
            handler(*args[:-1], msg)
            self.lock.release()

        return safe

    def listen(self):
        for handle in self.handles.values():
            handle.join()


class Producer:

    def __init__(self, server, serializer) -> None:
        self.server = server
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(server, credentials=pika.PlainCredentials("ubuntu", "ubuntu")
                                      ))
        self.channel = self.connection.channel()
        self.serializer = serializer

    def publish(self, exchange, message):
        bytes_obj = self.serializer(message)
        self.channel.basic_publish(
            exchange=exchange, routing_key='', body=bytes_obj)
