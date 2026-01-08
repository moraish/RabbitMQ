import pika
import sys
# Establish connection to RabbitMQ server
connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost') 
)
channel = connection.channel()

# Declare exchange of type 'fanout'
channel.exchange_declare(exchange='logs', exchange_type='fanout')

message = "info: Hello World!"

# Send message to the exchange
channel.basic_publish(exchange='logs',
                      routing_key='', # routing_key is ignored for fanout exchanges
                      body=message)

print(f" [x] Sent {message}")

# Close the connection
connection.close()