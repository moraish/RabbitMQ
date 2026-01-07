import pika

# connect to server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# declare a queue
channel.queue_declare(queue='hello')

# callback function to process received messages
def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    # print("ch:", ch)
    # print("method:", method)
    # print("properties:", properties)

channel.basic_consume(queue='hello',
                      auto_ack=True,
                      on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()

