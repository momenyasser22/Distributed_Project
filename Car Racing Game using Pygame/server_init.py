import pika

import urllib.request

external_ip = urllib.request.urlopen('https://ident.me').read().decode('utf8')


connection = pika.BlockingConnection(pika.ConnectionParameters(external_ip, credentials=pika.PlainCredentials("ubuntu", "ubuntu")
                                                               ))
channel = connection.channel()
channel.exchange_declare("events", exchange_type="fanout")
channel.exchange_declare("chat", exchange_type="fanout")
