import threading
class ConnectionHandle:

    def __init__(self, connection, channel, exchange, queue):
        self.connection = connection
        self.channel = channel
        self.exchange = exchange
        self.queue = queue
        self.thread = None

    def start(self):
        self.thread = threading.Thread(target=self.channel.start_consuming)
        self.thread.start()

    
    def join(self):
        self.thread.join()
        
    
    def stop(self):
        self.channel.stop_consuming()

    def delete(self):
        self.channel.queue_delete(self.queue)