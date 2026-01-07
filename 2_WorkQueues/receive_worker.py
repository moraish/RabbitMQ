import pika
import time
# connect to server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# declare a queue
channel.queue_declare(queue='hello', durable=True)

# callback function to process received messages
def callback(ch, method, properties, body):
    print(f"[x] Received {body.decode()}")
    time.sleep(body.count(b'.'))
    print("[x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)

# fair dispatch
channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue='hello',
                    on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
