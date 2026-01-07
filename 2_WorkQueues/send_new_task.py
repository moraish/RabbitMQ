import sys
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# declare a durable queue
queue = channel.queue_declare(queue='hello', durable=True)


# declare a persistent message
message = ' '.join(sys.argv[1:]) or "Hello World!"
channel.basic_publish(exchange='',
                    routing_key='hello',
                    body=message,
                    properties=pika.BasicProperties(
                        delivery_mode=pika.DeliveryMode.Persistent
                    ))

print(f"[x] Sent {message}", message)

connection.close()