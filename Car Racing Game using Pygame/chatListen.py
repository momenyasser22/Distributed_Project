from pikachu import Consumer


def chat_handler(channel, method, properties, body):
    print(body)


def main():
    consumer = Consumer("localhost")
    consumer.subscribe("events", event_handler=chat_handler,
                       deserializer=lambda x: x.decode('utf-8'))
    consumer.listen()


if __name__ == "__main__":
    main()
