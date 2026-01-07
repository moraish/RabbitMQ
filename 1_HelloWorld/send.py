import pika

# connect to server
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# declare a queue
channel.queue_declare(queue='hello')

# publish a message
channel.basic_publish(exchange='',
                      routing_key='hello',
                      body="Hello World!")

print(" [x] Sent 'Hello World!'")

# close the connection
connection.close()