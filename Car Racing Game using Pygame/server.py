from pikachu import Producer, Consumer
import pikachu
from TokenManger import TokenManager

import urllib.request

external_ip = urllib.request.urlopen(
    'https://ident.me').read().decode('utf8')

producer = Producer(external_ip, pikachu.serializeJSON)
consumer = Consumer(external_ip)
uuid2id = dict()
counter = 0


def handle_id_request(body):
    global counter
    global uuid2id
    global producer
    uuid = body.get("token").get("uuid")
    token_manager = TokenManager(token_lifetime_minutes=30)
    message = {
        "header": "id-response",
        "uuid": uuid
    }
    if uuid in uuid2id.keys():
        message["id"] = uuid2id[uuid]
        print(message)
    else:
        message["id"] = counter
        print(message)
        uuid2id[uuid] = counter
    counter += 1

    producer.publish("events", message)


headerHandlers = {
    "id-request": handle_id_request
}


def main():
    global consumer
    global producer
    consumer.subscribe("events", handler, pikachu.deserializeJSON)

    print(external_ip)
    consumer.listen()


def handler(channel, method, properties, body):
    header = body.get("header")
    messageHandler = headerHandlers.get(header, None)
    if messageHandler is not None:
        messageHandler(body)


if __name__ == "__main__":
    main()
